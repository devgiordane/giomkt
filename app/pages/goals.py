"""Goals tracking page."""

from datetime import date

import dash
from dash import html, dcc, callback, Output, Input, State, no_update, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from sqlalchemy import func, extract

dash.register_page(__name__, path="/goals", name="Metas")

MONTHS = [
    {"label": "Janeiro", "value": 1}, {"label": "Fevereiro", "value": 2},
    {"label": "Março", "value": 3}, {"label": "Abril", "value": 4},
    {"label": "Maio", "value": 5}, {"label": "Junho", "value": 6},
    {"label": "Julho", "value": 7}, {"label": "Agosto", "value": 8},
    {"label": "Setembro", "value": 9}, {"label": "Outubro", "value": 10},
    {"label": "Novembro", "value": 11}, {"label": "Dezembro", "value": 12},
]

layout = dbc.Container([
    dcc.Store(id="goals-refresh", data=0),

    # Add/Edit goal modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Definir Meta")),
        dbc.ModalBody([
            dbc.Alert(id="goals-add-alert", is_open=False, color="danger"),
            dbc.Row([
                dbc.Col([dbc.Label("Produto *"), dcc.Dropdown(id="goals-add-product")], md=12, className="mb-3"),
            ]),
            dbc.Row([
                dbc.Col([dbc.Label("Mês"), dcc.Dropdown(id="goals-add-month", options=MONTHS, value=date.today().month, clearable=False)], md=6, className="mb-3"),
                dbc.Col([dbc.Label("Ano"), dbc.Input(id="goals-add-year", type="number", value=date.today().year, min=2020, max=2030)], md=6, className="mb-3"),
            ]),
            dbc.Row([
                dbc.Col([dbc.Label("Meta de vendas (qtd)"), dbc.Input(id="goals-add-sales", type="number", min=0)], md=4, className="mb-3"),
                dbc.Col([dbc.Label("Meta de receita (R$)"), dbc.Input(id="goals-add-revenue", type="number", min=0, step=0.01)], md=4, className="mb-3"),
                dbc.Col([dbc.Label("Meta de comissão (R$)"), dbc.Input(id="goals-add-commission", type="number", min=0, step=0.01)], md=4, className="mb-3"),
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="goals-add-cancel", color="secondary", className="me-2"),
            dbc.Button("Salvar", id="goals-add-save", color="primary"),
        ]),
    ], id="goals-add-modal", is_open=False),

    # Header
    dbc.Row([
        dbc.Col(html.H2([html.I(className="bi bi-bullseye me-2"), "Metas"]), md=6),
        dbc.Col(
            dbc.Button([html.I(className="bi bi-plus-circle me-2"), "Definir Meta"],
                       id="goals-open-add", color="primary"),
            md=6, className="text-end",
        ),
    ], className="mb-4 mt-2 align-items-center"),

    # Month/Year selector
    dbc.Row([
        dbc.Col([dbc.Label("Mês:"), dcc.Dropdown(id="goals-sel-month", options=MONTHS, value=date.today().month, clearable=False)], md=3, className="mb-3"),
        dbc.Col([dbc.Label("Ano:"), dbc.Input(id="goals-sel-year", type="number", value=date.today().year, min=2020, max=2030)], md=2, className="mb-3"),
    ]),

    # View Mode Toggle
    dbc.Row([
        dbc.Col([
            dbc.RadioItems(
                id="goals-view-mode",
                options=[
                    {"label": "Visão Geral (Produtor)", "value": "total"},
                    {"label": "Minha Visão (Coprodutor/Comissão)", "value": "commission"},
                ],
                value="commission",
                inline=True,
                className="mb-3"
            )
        ], md=12)
    ]),

    # Progress bars
    html.Div(id="goals-progress", className="mb-4"),

    # Chart
    dcc.Graph(id="goals-chart", config={"displayModeBar": False}),

    dbc.Toast(id="goals-toast", header="Metas", is_open=False, dismissable=True, duration=3000,
              style={"position": "fixed", "bottom": "1rem", "right": "1rem", "zIndex": 9999}),
], fluid=True)


@callback(
    Output("goals-progress", "children"),
    Output("goals-chart", "figure"),
    Input("goals-refresh", "data"),
    Input("goals-sel-month", "value"),
    Input("goals-sel-year", "value"),
    Input("goals-view-mode", "value"),
)
def load_goals(_refresh, month, year, view_mode):
    from app.database import get_session, ProductGoal, Sale, Product

    month = month or date.today().month
    year = year or date.today().year

    with get_session() as session:
        goals = session.query(ProductGoal).filter_by(month=month, year=year).all()

        progress_items = []
        chart_names = []
        chart_targets = []
        chart_actuals = []

        for g in goals:
            product = session.get(Product, g.product_id)
            if not product:
                continue

            actual_count = session.query(func.coalesce(func.sum(Sale.quantity), 0)).filter(
                Sale.product_id == g.product_id,
                extract("month", Sale.date) == month,
                extract("year", Sale.date) == year,
            ).scalar() or 0

            actual_revenue = session.query(func.coalesce(func.sum(Sale.value), 0)).filter(
                Sale.product_id == g.product_id,
                extract("month", Sale.date) == month,
                extract("year", Sale.date) == year,
            ).scalar() or 0
            
            actual_commission = session.query(func.coalesce(func.sum(Sale.commission_value), 0)).filter(
                Sale.product_id == g.product_id,
                extract("month", Sale.date) == month,
                extract("year", Sale.date) == year,
            ).scalar() or 0

            # Historic Projection
            from datetime import timedelta
            past_months_revenue = session.query(func.coalesce(func.sum(Sale.value), 0)).filter(
                Sale.product_id == g.product_id,
                Sale.date >= date.today() - timedelta(days=90),
                Sale.date < date.today().replace(day=1)
            ).scalar() or 0
            
            past_months_commission = session.query(func.coalesce(func.sum(Sale.commission_value), 0)).filter(
                Sale.product_id == g.product_id,
                Sale.date >= date.today() - timedelta(days=90),
                Sale.date < date.today().replace(day=1)
            ).scalar() or 0
            
            # Simple avg 3 months
            avg_revenue = past_months_revenue / 3 if past_months_revenue else 0
            avg_commission = past_months_commission / 3 if past_months_commission else 0

            # Sales progress
            sales_pct = min(int(actual_count / g.sales_target * 100), 100) if g.sales_target else 0
            
            is_comm = view_mode == "commission"
            
            target_val = g.commission_target if is_comm else g.revenue_target
            actual_val = actual_commission if is_comm else actual_revenue
            avg_val = avg_commission if is_comm else avg_revenue
            
            val_pct = min(int(actual_val / target_val * 100), 100) if target_val else 0

            color = "success" if sales_pct >= 100 else "primary" if sales_pct >= 50 else "warning"
            val_color = "success" if val_pct >= 100 else "primary" if val_pct >= 50 else "warning"

            progress_items.append(
                dbc.Card(dbc.CardBody([
                    html.H5(product.name, className="mb-2"),
                    html.P(f"Vendas: {actual_count} / {g.sales_target}", className="mb-1") if g.sales_target else None,
                    dbc.Progress(value=sales_pct, color=color, className="mb-2",
                                 label=f"{sales_pct}%", style={"height": "24px"}) if g.sales_target else None,
                    
                    html.P(f"{'Comissão' if is_comm else 'Receita'}: R$ {actual_val:,.2f} / R$ {target_val:,.2f}", className="mb-1") if target_val else None,
                    dbc.Progress(value=val_pct, color=val_color, className="mb-2",
                                 label=f"{val_pct}%", style={"height": "24px"}) if target_val else None,
                                 
                    html.P([
                        html.I(className="bi bi-graph-up me-1 text-info"),
                        f"Projeção baseada na média (últimos 3 meses): R$ {avg_val:,.2f}"
                    ], className="mb-0 mt-3 text-muted small") if avg_val > 0 else None
                ]), className="kpi-card mb-3")
            )

            chart_names.append(product.name)
            chart_targets.append(target_val or 0)
            chart_actuals.append(actual_val)

    if not progress_items:
        progress_items = [dbc.Alert("Nenhuma meta definida para este período.", color="info")]

    # Chart
    fig = go.Figure()
    if chart_names:
        fig.add_trace(go.Bar(name="Meta " + ("Comissão" if view_mode == "commission" else "Receita"), x=chart_names, y=chart_targets, marker_color="#0d6efd"))
        fig.add_trace(go.Bar(name="Atual " + ("Comissão" if view_mode == "commission" else "Receita"), x=chart_names, y=chart_actuals, marker_color="#198754"))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        barmode="group",
        title="Meta vs Vendas",
        margin=dict(t=40, b=40, l=40, r=20),
        height=350,
    )

    return progress_items, fig


def _product_options():
    from app.database import get_session, Product
    with get_session() as session:
        products = session.query(Product).filter_by(active=True).order_by(Product.name).all()
        return [{"label": p.name, "value": p.id} for p in products]


@callback(
    Output("goals-add-modal", "is_open"),
    Output("goals-add-product", "options"),
    Output("goals-add-product", "value"),
    Output("goals-add-month", "value"),
    Output("goals-add-year", "value"),
    Output("goals-add-sales", "value"),
    Output("goals-add-revenue", "value"),
    Output("goals-add-commission", "value"),
    Input("goals-open-add", "n_clicks"),
    Input("goals-add-cancel", "n_clicks"),
    State("goals-sel-month", "value"),
    State("goals-sel-year", "value"),
    prevent_initial_call=True,
)
def toggle_add(_o, _c, sel_month, sel_year):
    if ctx.triggered_id == "goals-open-add":
        return True, _product_options(), None, sel_month or date.today().month, sel_year or date.today().year, None, None, None
    return False, no_update, no_update, no_update, no_update, no_update, no_update, no_update


@callback(
    Output("goals-add-alert", "children"),
    Output("goals-add-alert", "is_open"),
    Output("goals-add-modal", "is_open", allow_duplicate=True),
    Output("goals-refresh", "data", allow_duplicate=True),
    Output("goals-toast", "children", allow_duplicate=True),
    Output("goals-toast", "is_open", allow_duplicate=True),
    Input("goals-add-save", "n_clicks"),
    State("goals-add-product", "value"),
    State("goals-add-month", "value"),
    State("goals-add-year", "value"),
    State("goals-add-sales", "value"),
    State("goals-add-revenue", "value"),
    State("goals-add-commission", "value"),
    State("goals-refresh", "data"),
    prevent_initial_call=True,
)
def save_goal(_n, product_id, month, year, sales_target, revenue_target, commission_target, refresh):
    if not product_id:
        return "Selecione um produto.", True, no_update, no_update, no_update, no_update

    from app.database import get_session, ProductGoal

    try:
        with get_session() as session:
            existing = session.query(ProductGoal).filter_by(
                product_id=product_id, month=month, year=year,
            ).first()

            if existing:
                existing.sales_target = int(sales_target) if sales_target else 0
                existing.revenue_target = float(revenue_target) if revenue_target else 0
                existing.commission_target = float(commission_target) if commission_target else 0
            else:
                session.add(ProductGoal(
                    product_id=product_id,
                    month=month,
                    year=year,
                    sales_target=int(sales_target) if sales_target else 0,
                    revenue_target=float(revenue_target) if revenue_target else 0,
                    commission_target=float(commission_target) if commission_target else 0,
                ))

        return no_update, False, False, (refresh or 0) + 1, "Meta salva!", True
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update, no_update, no_update
