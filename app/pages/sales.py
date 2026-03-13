"""Sales listing page."""

from datetime import date, datetime

import dash
from dash import html, dcc, callback, Output, Input, State, no_update, ctx
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from sqlalchemy import func, extract

dash.register_page(__name__, path="/sales", name="Vendas")

layout = dbc.Container([
    dcc.Store(id="sales-refresh", data=0),
    dcc.Store(id="sales-del-id"),

    # Add modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Nova Venda")),
        dbc.ModalBody([
            dbc.Alert(id="sales-add-alert", is_open=False, color="danger"),
            dbc.Row([
                dbc.Col([dbc.Label("Produto *"), dcc.Dropdown(id="sales-add-product")], md=6, className="mb-3"),
                dbc.Col([dbc.Label("Data"), dbc.Input(id="sales-add-date", type="date", value=date.today().isoformat())], md=6, className="mb-3"),
            ]),
            dbc.Row([
                dbc.Col([dbc.Label("Valor (R$) *"), dbc.Input(id="sales-add-value", type="number", min=0, step=0.01)], md=4, className="mb-3"),
                dbc.Col([dbc.Label("Comissão (R$)"), dbc.Input(id="sales-add-commission", type="number", min=0, step=0.01)], md=4, className="mb-3"),
                dbc.Col([dbc.Label("Quantidade"), dbc.Input(id="sales-add-qty", type="number", min=1, value=1)], md=4, className="mb-3"),
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="sales-add-cancel", color="secondary", className="me-2"),
            dbc.Button("Salvar", id="sales-add-save", color="primary"),
        ]),
    ], id="sales-add-modal", is_open=False),

    # Delete confirm
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Confirmar exclusão")),
        dbc.ModalBody("Excluir esta venda?"),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="sales-del-cancel", color="secondary", className="me-2"),
            dbc.Button("Excluir", id="sales-del-confirm", color="danger"),
        ]),
    ], id="sales-del-modal", is_open=False),

    # Header
    dbc.Row([
        dbc.Col(html.H2([html.I(className="bi bi-cart-check me-2"), "Vendas"]), md=8),
        dbc.Col(
            dbc.Button([html.I(className="bi bi-plus-circle me-2"), "Nova Venda"],
                       id="sales-open-add", color="primary"),
            md=4, className="text-end",
        ),
    ], className="mb-4 mt-2 align-items-center"),

    # Filters
    dbc.Row([
        dbc.Col([dbc.Label("Produto:"), dcc.Dropdown(id="sales-filter-product", placeholder="Todos")], md=3, className="mb-3"),
        dbc.Col([dbc.Label("Mês/Ano:"), dcc.Dropdown(id="sales-filter-month", placeholder="Todos")], md=3, className="mb-3"),
    ]),

    # KPIs
    html.Div(id="sales-kpis", className="mb-4"),

    # Table
    html.Div(id="sales-table"),

    dbc.Toast(id="sales-toast", header="Vendas", is_open=False, dismissable=True, duration=3000,
              style={"position": "fixed", "bottom": "1rem", "right": "1rem", "zIndex": 9999}),
], fluid=True)


def _product_options():
    from app.database import get_session, Product
    with get_session() as session:
        products = session.query(Product).filter_by(active=True).order_by(Product.name).all()
        return [{"label": p.name, "value": p.id} for p in products]


@callback(
    Output("sales-kpis", "children"),
    Output("sales-table", "children"),
    Output("sales-filter-product", "options"),
    Output("sales-filter-month", "options"),
    Input("sales-refresh", "data"),
    Input("sales-filter-product", "value"),
    Input("sales-filter-month", "value"),
)
def load_sales(_refresh, prod_filter, month_filter):
    from app.database import get_session, Sale, Product

    with get_session() as session:
        q = session.query(Sale).join(Product)

        if prod_filter:
            q = q.filter(Sale.product_id == prod_filter)

        if month_filter:
            y, m = month_filter.split("-")
            q = q.filter(extract("year", Sale.date) == int(y), extract("month", Sale.date) == int(m))

        sales = q.order_by(Sale.date.desc()).all()

        data = []
        total_value = 0
        total_commission = 0
        total_qty = 0

        for s in sales:
            data.append({
                "id": s.id,
                "product": s.product.name if s.product else "—",
                "date": s.date.isoformat() if s.date else "",
                "value": s.value,
                "commission": s.commission_value,
                "qty": s.quantity,
                "source": "Eduzz" if s.source == "eduzz_api" else "Manual",
            })
            total_value += s.value or 0
            total_commission += s.commission_value or 0
            total_qty += s.quantity or 0

        # Month options
        all_dates = session.query(
            func.distinct(func.strftime("%Y-%m", Sale.date))
        ).order_by(func.strftime("%Y-%m", Sale.date).desc()).all()
        month_opts = [{"label": d[0], "value": d[0]} for d in all_dates if d[0]]

    prod_opts = _product_options()
    ticket = total_value / total_qty if total_qty else 0

    kpis = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Total Vendas", className="kpi-label"),
            html.H3(str(total_qty), className="kpi-value"),
        ]), className="kpi-card"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Receita Total", className="kpi-label"),
            html.H3(f"R$ {total_value:,.2f}", className="kpi-value"),
        ]), className="kpi-card"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Comissão Total", className="kpi-label"),
            html.H3(f"R$ {total_commission:,.2f}", className="kpi-value"),
        ]), className="kpi-card"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Ticket Médio", className="kpi-label"),
            html.H3(f"R$ {ticket:,.2f}", className="kpi-value"),
        ]), className="kpi-card"), md=3),
    ])

    if not data:
        return kpis, dbc.Alert("Nenhuma venda registrada.", color="info"), prod_opts, month_opts

    col_defs = [
        {"field": "product", "headerName": "Produto", "flex": 2},
        {"field": "date", "headerName": "Data", "flex": 1},
        {"field": "value", "headerName": "Valor (R$)", "flex": 1,
         "valueFormatter": {"function": "d3.format(',.2f')(params.value)"}},
        {"field": "commission", "headerName": "Comissão (R$)", "flex": 1,
         "valueFormatter": {"function": "d3.format(',.2f')(params.value)"}},
        {"field": "qty", "headerName": "Qtd", "flex": 0.5},
        {"field": "source", "headerName": "Origem", "flex": 0.8},
    ]

    actions = dbc.Row([dbc.Col([
        dbc.Button([html.I(className="bi bi-trash me-1"), "Excluir"], id="sales-del-btn", size="sm", color="danger"),
    ], className="mb-2")])

    grid = dag.AgGrid(
        id="sales-grid", rowData=data, columnDefs=col_defs,
        defaultColDef={"sortable": True, "filter": True, "resizable": True},
        className="ag-theme-alpine-dark", style={"height": "400px"},
        dashGridOptions={"rowSelection": "single"},
    )

    return kpis, html.Div([actions, grid]), prod_opts, month_opts


# Add
@callback(
    Output("sales-add-modal", "is_open"),
    Output("sales-add-product", "options"), Output("sales-add-product", "value"),
    Output("sales-add-date", "value"), Output("sales-add-value", "value"),
    Output("sales-add-commission", "value"), Output("sales-add-qty", "value"),
    Input("sales-open-add", "n_clicks"), Input("sales-add-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_add(_o, _c):
    if ctx.triggered_id == "sales-open-add":
        return True, _product_options(), None, date.today().isoformat(), None, None, 1
    return False, no_update, no_update, no_update, no_update, no_update, no_update


@callback(
    Output("sales-add-alert", "children"), Output("sales-add-alert", "is_open"),
    Output("sales-add-modal", "is_open", allow_duplicate=True),
    Output("sales-refresh", "data", allow_duplicate=True),
    Output("sales-toast", "children", allow_duplicate=True), Output("sales-toast", "is_open", allow_duplicate=True),
    Input("sales-add-save", "n_clicks"),
    State("sales-add-product", "value"), State("sales-add-date", "value"),
    State("sales-add-value", "value"), State("sales-add-commission", "value"),
    State("sales-add-qty", "value"), State("sales-refresh", "data"),
    prevent_initial_call=True,
)
def save_add(_n, product_id, sale_date, value, commission, qty, refresh):
    if not product_id:
        return "Selecione um produto.", True, no_update, no_update, no_update, no_update
    if not value:
        return "Valor é obrigatório.", True, no_update, no_update, no_update, no_update

    from app.database import get_session, Sale

    try:
        with get_session() as session:
            session.add(Sale(
                product_id=product_id,
                date=date.fromisoformat(sale_date) if sale_date else date.today(),
                value=float(value),
                commission_value=float(commission) if commission else 0,
                quantity=int(qty) if qty else 1,
                source="manual",
            ))
        return no_update, False, False, (refresh or 0) + 1, "Venda registrada!", True
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update, no_update, no_update


# Delete
@callback(
    Output("sales-del-modal", "is_open"), Output("sales-del-id", "data"),
    Input("sales-del-btn", "n_clicks"), Input("sales-del-cancel", "n_clicks"),
    State("sales-grid", "selectedRows"),
    prevent_initial_call=True,
)
def toggle_delete(_d, _c, selected):
    if ctx.triggered_id == "sales-del-cancel" or not selected:
        return False, no_update
    return True, selected[0]["id"]


@callback(
    Output("sales-del-modal", "is_open", allow_duplicate=True),
    Output("sales-refresh", "data", allow_duplicate=True),
    Output("sales-toast", "children", allow_duplicate=True), Output("sales-toast", "is_open", allow_duplicate=True),
    Input("sales-del-confirm", "n_clicks"),
    State("sales-del-id", "data"), State("sales-refresh", "data"),
    prevent_initial_call=True,
)
def confirm_delete(_n, sid, refresh):
    if not sid:
        return False, no_update, no_update, no_update
    from app.database import get_session, Sale
    with get_session() as session:
        s = session.get(Sale, sid)
        if s:
            session.delete(s)
    return False, (refresh or 0) + 1, "Venda excluída.", True
