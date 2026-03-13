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
                dbc.Col([dbc.Label("Meta de vendas (qtd)"), dbc.Input(id="goals-add-sales", type="number", min=0)], md=6, className="mb-3"),
                dbc.Col([dbc.Label("Meta de receita (R$)"), dbc.Input(id="goals-add-revenue", type="number", min=0, step=0.01)], md=6, className="mb-3"),
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
)
def load_goals(_refresh, month, year):
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

            # Sales progress
            sales_pct = min(int(actual_count / g.sales_target * 100), 100) if g.sales_target else 0
            # Revenue progress
            rev_pct = min(int(actual_revenue / g.revenue_target * 100), 100) if g.revenue_target else 0

            color = "success" if sales_pct >= 100 else "primary" if sales_pct >= 50 else "warning"

            progress_items.append(
                dbc.Card(dbc.CardBody([
                    html.H5(product.name, className="mb-2"),
                    html.P(f"Vendas: {actual_count} / {g.sales_target}", className="mb-1") if g.sales_target else None,
                    dbc.Progress(value=sales_pct, color=color, className="mb-2",
                                 label=f"{sales_pct}%", style={"height": "24px"}) if g.sales_target else None,
                    html.P(f"Receita: R$ {actual_revenue:,.2f} / R$ {g.revenue_target:,.2f}", className="mb-1") if g.revenue_target else None,
                    dbc.Progress(value=rev_pct, color=color, className="mb-2",
                                 label=f"{rev_pct}%", style={"height": "24px"}) if g.revenue_target else None,
                ]), className="kpi-card mb-3")
            )

            chart_names.append(product.name)
            chart_targets.append(g.sales_target or 0)
            chart_actuals.append(int(actual_count))

    if not progress_items:
        progress_items = [dbc.Alert("Nenhuma meta definida para este período.", color="info")]

    # Chart
    fig = go.Figure()
    if chart_names:
        fig.add_trace(go.Bar(name="Meta", x=chart_names, y=chart_targets, marker_color="#0d6efd"))
        fig.add_trace(go.Bar(name="Vendas", x=chart_names, y=chart_actuals, marker_color="#198754"))
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
    Input("goals-open-add", "n_clicks"),
    Input("goals-add-cancel", "n_clicks"),
    State("goals-sel-month", "value"),
    State("goals-sel-year", "value"),
    prevent_initial_call=True,
)
def toggle_add(_o, _c, sel_month, sel_year):
    if ctx.triggered_id == "goals-open-add":
        return True, _product_options(), None, sel_month or date.today().month, sel_year or date.today().year, None, None
    return False, no_update, no_update, no_update, no_update, no_update, no_update


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
    State("goals-refresh", "data"),
    prevent_initial_call=True,
)
def save_goal(_n, product_id, month, year, sales_target, revenue_target, refresh):
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
            else:
                session.add(ProductGoal(
                    product_id=product_id,
                    month=month,
                    year=year,
                    sales_target=int(sales_target) if sales_target else 0,
                    revenue_target=float(revenue_target) if revenue_target else 0,
                ))

        return no_update, False, False, (refresh or 0) + 1, "Meta salva!", True
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update, no_update, no_update
