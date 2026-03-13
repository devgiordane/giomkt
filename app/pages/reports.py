"""Reports generation page."""

from datetime import date, timedelta

import dash
from dash import html, dcc, callback, Output, Input, State, no_update, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from sqlalchemy import func, extract

dash.register_page(__name__, path="/reports", name="Relatórios")

layout = dbc.Container([
    dcc.Store(id="rpt-data-store"),

    # Header
    dbc.Row([
        dbc.Col(html.H2([html.I(className="bi bi-file-earmark-text me-2"), "Relatórios"]), md=12),
    ], className="mb-4 mt-2"),

    # Filters
    dbc.Row([
        dbc.Col([dbc.Label("Conta Eduzz:"), dcc.Dropdown(id="rpt-account", placeholder="Todas")], md=3, className="mb-3"),
        dbc.Col([dbc.Label("Produto:"), dcc.Dropdown(id="rpt-product", placeholder="Todos")], md=3, className="mb-3"),
        dbc.Col([dbc.Label("De:"), dbc.Input(id="rpt-start", type="date", value=(date.today().replace(day=1)).isoformat())], md=2, className="mb-3"),
        dbc.Col([dbc.Label("Até:"), dbc.Input(id="rpt-end", type="date", value=date.today().isoformat())], md=2, className="mb-3"),
        dbc.Col([
            dbc.Label("\u00a0"),
            html.Div([
                dbc.Button([html.I(className="bi bi-bar-chart me-1"), "Gerar"], id="rpt-generate", color="primary", className="me-2"),
                dbc.Button([html.I(className="bi bi-robot me-1"), "Gerar com IA"], id="rpt-ai-generate", color="info"),
            ]),
        ], md=2, className="mb-3"),
    ]),

    # Output
    html.Div(id="rpt-output"),

    # AI report output
    dcc.Loading(html.Div(id="rpt-ai-output"), type="circle", color="#0d6efd"),
], fluid=True)


def _account_options():
    from app.database import get_session, EduzzAccount
    with get_session() as session:
        return [{"label": a.name, "value": a.id}
                for a in session.query(EduzzAccount).filter_by(active=True).order_by(EduzzAccount.name).all()]


def _product_options(account_id=None):
    from app.database import get_session, Product
    with get_session() as session:
        q = session.query(Product).filter_by(active=True)
        if account_id:
            q = q.filter_by(account_id=account_id)
        return [{"label": p.name, "value": p.id} for p in q.order_by(Product.name).all()]


@callback(
    Output("rpt-account", "options"),
    Output("rpt-product", "options"),
    Input("rpt-account", "value"),
)
def update_filters(account_id):
    return _account_options(), _product_options(account_id)


@callback(
    Output("rpt-output", "children"),
    Output("rpt-data-store", "data"),
    Input("rpt-generate", "n_clicks"),
    State("rpt-account", "value"),
    State("rpt-product", "value"),
    State("rpt-start", "value"),
    State("rpt-end", "value"),
    prevent_initial_call=True,
)
def generate_report(_n, account_id, product_id, start_str, end_str):
    from app.database import get_session, Sale, Product, EduzzAccount

    start = date.fromisoformat(start_str) if start_str else date.today().replace(day=1)
    end = date.fromisoformat(end_str) if end_str else date.today()

    with get_session() as session:
        q = session.query(Sale).join(Product).filter(Sale.date.between(start, end))
        if product_id:
            q = q.filter(Sale.product_id == product_id)
        elif account_id:
            q = q.filter(Product.account_id == account_id)

        sales = q.order_by(Sale.date).all()

        total_qty = sum(s.quantity or 0 for s in sales)
        total_value = sum(s.value or 0 for s in sales)
        total_commission = sum(s.commission_value or 0 for s in sales)
        ticket = total_value / total_qty if total_qty else 0

        # Group by date for chart
        daily = {}
        daily_commission = {}
        for s in sales:
            key = s.date.isoformat() if s.date else "?"
            daily[key] = daily.get(key, 0) + (s.value or 0)
            daily_commission[key] = daily_commission.get(key, 0) + (s.commission_value or 0)

        # Group by product for table
        by_product = {}
        for s in sales:
            pname = s.product.name if s.product else "?"
            if pname not in by_product:
                by_product[pname] = {"qty": 0, "value": 0, "commission": 0}
            by_product[pname]["qty"] += s.quantity or 0
            by_product[pname]["value"] += s.value or 0
            by_product[pname]["commission"] += s.commission_value or 0

    # Store data for AI
    store_data = {
        "total_qty": total_qty, "total_value": total_value,
        "total_commission": total_commission, "ticket": ticket,
        "start": start.isoformat(), "end": end.isoformat(),
        "by_product": by_product,
    }

    # KPIs
    kpis = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Total Vendas", className="kpi-label"),
            html.H3(str(total_qty), className="kpi-value"),
        ]), className="kpi-card"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Receita Total do Produtor", className="kpi-label"),
            html.H3(f"R$ {total_value:,.2f}", className="kpi-value"),
        ]), className="kpi-card"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Meus Ganhos (Receita / Coprodutor)", className="kpi-label"),
            html.H3(f"R$ {total_commission:,.2f}", className="kpi-value", style={"color": "#198754"}),
        ]), className="kpi-card"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Ticket Médio", className="kpi-label"),
            html.H3(f"R$ {ticket:,.2f}", className="kpi-value"),
        ]), className="kpi-card"), md=3),
    ], className="mb-4")

    # Chart
    fig = go.Figure()
    if daily:
        dates = sorted(daily.keys())
        fig.add_trace(go.Scatter(
            x=dates, y=[daily[d] for d in dates],
            mode="lines+markers", name="Receita do Produtor",
            line=dict(color="#0d6efd"),
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=[daily_commission[d] for d in dates],
            mode="lines+markers", name="Meus Ganhos",
            line=dict(color="#198754"),
        ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title="Receita e Meus Ganhos por Dia",
        margin=dict(t=40, b=40, l=40, r=20),
        height=300,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Product summary table
    rows = []
    for pname, vals in by_product.items():
        rows.append(html.Tr([
            html.Td(pname),
            html.Td(str(vals["qty"])),
            html.Td(f"R$ {vals['value']:,.2f}"),
            html.Td(f"R$ {vals['commission']:,.2f}", style={"color": "#198754", "fontWeight": "bold"}),
        ]))

    product_table = dbc.Table([
        html.Thead(html.Tr([html.Th("Produto"), html.Th("Vendas"), html.Th("Receita (Produtor)"), html.Th("Meus Ganhos")])),
        html.Tbody(rows),
    ], bordered=True, hover=True, responsive=True, className="mt-3") if rows else None

    return html.Div([kpis, dcc.Graph(figure=fig, config={"displayModeBar": False}), product_table]), store_data


@callback(
    Output("rpt-ai-output", "children"),
    Input("rpt-ai-generate", "n_clicks"),
    State("rpt-data-store", "data"),
    prevent_initial_call=True,
)
def generate_ai_report(_n, data):
    if not data:
        return dbc.Alert("Gere o relatório primeiro antes de usar a IA.", color="warning")

    text = (
        f"Período: {data.get('start', '')} a {data.get('end', '')}\n"
        f"Total vendas: {data.get('total_qty', 0)}\n"
        f"Receita total: R$ {data.get('total_value', 0):,.2f}\n"
        f"Comissão total: R$ {data.get('total_commission', 0):,.2f}\n"
        f"Ticket médio: R$ {data.get('ticket', 0):,.2f}\n\n"
        "Por produto:\n"
    )
    for pname, vals in (data.get("by_product") or {}).items():
        text += f"- {pname}: {vals['qty']} vendas, R$ {vals['value']:,.2f} receita, R$ {vals['commission']:,.2f} comissão\n"

    from app.services.ai_assistant import process_content
    result = process_content("summarize", text)

    if "error" in result:
        return dbc.Alert(result["error"], color="danger")

    summary = result.get("summary", "")
    points = result.get("key_points", [])

    return dbc.Card([
        dbc.CardHeader([html.I(className="bi bi-robot me-2"), "Relatório gerado por IA"]),
        dbc.CardBody([
            html.P(summary, style={"whiteSpace": "pre-wrap"}),
            html.Hr() if points else None,
            dbc.ListGroup([
                dbc.ListGroupItem([html.I(className="bi bi-check-circle me-2"), p])
                for p in points
            ], flush=True) if points else None,
            html.Div([
                dcc.Clipboard(target_id="rpt-ai-text", className="mt-2"),
                html.Div(summary, id="rpt-ai-text", style={"display": "none"}),
            ]),
        ]),
    ], className="mt-3")
