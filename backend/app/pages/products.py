"""Products listing page."""

import dash
from dash import html, dcc, callback, Output, Input, State, no_update, ctx
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

dash.register_page(__name__, path="/products", name="Produtos")

layout = dbc.Container([
    dcc.Store(id="prod-refresh", data=0),
    dcc.Store(id="prod-edit-id"),
    dcc.Store(id="prod-del-id"),

    # Add modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Novo Produto")),
        dbc.ModalBody([
            dbc.Alert(id="prod-add-alert", is_open=False, color="danger"),
            dbc.Row([
                dbc.Col([dbc.Label("Nome *"), dbc.Input(id="prod-add-name")], md=6, className="mb-3"),
                dbc.Col([dbc.Label("Conta Eduzz *"), dcc.Dropdown(id="prod-add-account")], md=6, className="mb-3"),
            ]),
            dbc.Row([
                dbc.Col([dbc.Label("ID Eduzz"), dbc.Input(id="prod-add-eduzz-id")], md=4, className="mb-3"),
                dbc.Col([dbc.Label("Preço (R$)"), dbc.Input(id="prod-add-price", type="number", min=0, step=0.01)], md=4, className="mb-3"),
                dbc.Col([dbc.Label("Comissão (%)"), dbc.Input(id="prod-add-commission", type="number", min=0, max=100, step=0.1)], md=4, className="mb-3"),
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="prod-add-cancel", color="secondary", className="me-2"),
            dbc.Button("Salvar", id="prod-add-save", color="primary"),
        ]),
    ], id="prod-add-modal", is_open=False),

    # Edit modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Editar Produto")),
        dbc.ModalBody([
            dbc.Alert(id="prod-edit-alert", is_open=False, color="danger"),
            dbc.Row([
                dbc.Col([dbc.Label("Nome *"), dbc.Input(id="prod-edit-name")], md=6, className="mb-3"),
                dbc.Col([dbc.Label("Conta Eduzz *"), dcc.Dropdown(id="prod-edit-account")], md=6, className="mb-3"),
            ]),
            dbc.Row([
                dbc.Col([dbc.Label("ID Eduzz"), dbc.Input(id="prod-edit-eduzz-id")], md=4, className="mb-3"),
                dbc.Col([dbc.Label("Preço (R$)"), dbc.Input(id="prod-edit-price", type="number", min=0, step=0.01)], md=4, className="mb-3"),
                dbc.Col([dbc.Label("Comissão (%)"), dbc.Input(id="prod-edit-commission", type="number", min=0, max=100, step=0.1)], md=4, className="mb-3"),
            ]),
            dbc.Checkbox(id="prod-edit-active", label="Ativo", value=True, className="mb-3"),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="prod-edit-cancel", color="secondary", className="me-2"),
            dbc.Button("Salvar", id="prod-edit-save", color="primary"),
        ]),
    ], id="prod-edit-modal", is_open=False),

    # Delete confirm
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Confirmar exclusão")),
        dbc.ModalBody("Excluir este produto e todas as vendas associadas?"),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="prod-del-cancel", color="secondary", className="me-2"),
            dbc.Button("Excluir", id="prod-del-confirm", color="danger"),
        ]),
    ], id="prod-del-modal", is_open=False),

    # Header
    dbc.Row([
        dbc.Col(html.H2([html.I(className="bi bi-box-seam me-2"), "Produtos"]), md=6),
        dbc.Col(html.Div([
            dbc.Button([html.I(className="bi bi-plus-circle me-2"), "Novo Produto"],
                       id="prod-open-add", color="primary", className="me-2"),
            dbc.Button([html.I(className="bi bi-gear me-1"), "Contas Eduzz"],
                       href="/eduzz/accounts", color="secondary", size="sm"),
        ], className="text-end"), md=6),
    ], className="mb-4 mt-2 align-items-center"),

    # Filter
    dbc.Row([
        dbc.Col([
            dbc.Label("Filtrar por conta:"),
            dcc.Dropdown(id="prod-filter-account", placeholder="Todas"),
        ], md=4, className="mb-3"),
    ]),

    html.Div(id="prod-table"),

    dbc.Toast(id="prod-toast", header="Produtos", is_open=False, dismissable=True, duration=3000,
              style={"position": "fixed", "bottom": "1rem", "right": "1rem", "zIndex": 9999}),
], fluid=True)


def _account_options():
    from app.database import get_session, EduzzAccount
    with get_session() as session:
        accounts = session.query(EduzzAccount).filter_by(active=True).order_by(EduzzAccount.name).all()
        return [{"label": a.name, "value": a.id} for a in accounts]


@callback(
    Output("prod-table", "children"),
    Output("prod-filter-account", "options"),
    Input("prod-refresh", "data"),
    Input("prod-filter-account", "value"),
)
def load_products(_refresh, account_filter):
    from app.database import get_session, Product, EduzzAccount

    with get_session() as session:
        q = session.query(Product)
        if account_filter:
            q = q.filter_by(account_id=account_filter)
        products = q.order_by(Product.name).all()

        data = []
        for p in products:
            data.append({
                "id": p.id,
                "name": p.name,
                "account": p.account.name if p.account else "—",
                "price": p.price,
                "commission": p.commission_percent,
                "active": "Sim" if p.active else "Não",
                "eduzz_id": p.product_id_eduzz or "",
            })

    opts = _account_options()

    if not data:
        return dbc.Alert("Nenhum produto cadastrado.", color="info"), opts

    col_defs = [
        {"field": "name", "headerName": "Produto", "flex": 2},
        {"field": "account", "headerName": "Conta Eduzz", "flex": 1.5},
        {"field": "price", "headerName": "Preço (R$)", "flex": 1,
         "valueFormatter": {"function": "d3.format(',.2f')(params.value)"}},
        {"field": "commission", "headerName": "Comissão %", "flex": 1},
        {"field": "active", "headerName": "Ativo", "flex": 0.7},
    ]

    actions = dbc.Row([dbc.Col([
        dbc.Button([html.I(className="bi bi-pencil me-1"), "Editar"], id="prod-edit-btn", size="sm", color="secondary", className="me-2"),
        dbc.Button([html.I(className="bi bi-trash me-1"), "Excluir"], id="prod-del-btn", size="sm", color="danger"),
    ], className="mb-2")])

    grid = dag.AgGrid(
        id="prod-grid", rowData=data, columnDefs=col_defs,
        defaultColDef={"sortable": True, "filter": True, "resizable": True},
        className="ag-theme-alpine-dark", style={"height": "400px"},
        dashGridOptions={"rowSelection": "single"},
    )

    return html.Div([actions, grid]), opts


# Add
@callback(
    Output("prod-add-modal", "is_open"),
    Output("prod-add-name", "value"), Output("prod-add-account", "options"), Output("prod-add-account", "value"),
    Output("prod-add-eduzz-id", "value"), Output("prod-add-price", "value"), Output("prod-add-commission", "value"),
    Input("prod-open-add", "n_clicks"), Input("prod-add-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_add(_o, _c):
    if ctx.triggered_id == "prod-open-add":
        return True, "", _account_options(), None, "", None, None
    return False, no_update, no_update, no_update, no_update, no_update, no_update


@callback(
    Output("prod-add-alert", "children"), Output("prod-add-alert", "is_open"),
    Output("prod-add-modal", "is_open", allow_duplicate=True),
    Output("prod-refresh", "data", allow_duplicate=True),
    Output("prod-toast", "children", allow_duplicate=True), Output("prod-toast", "is_open", allow_duplicate=True),
    Input("prod-add-save", "n_clicks"),
    State("prod-add-name", "value"), State("prod-add-account", "value"),
    State("prod-add-eduzz-id", "value"), State("prod-add-price", "value"), State("prod-add-commission", "value"),
    State("prod-refresh", "data"),
    prevent_initial_call=True,
)
def save_add(_n, name, account_id, eduzz_id, price, commission, refresh):
    if not name or not name.strip():
        return "Nome é obrigatório.", True, no_update, no_update, no_update, no_update
    if not account_id:
        return "Selecione uma conta.", True, no_update, no_update, no_update, no_update
    from app.database import get_session, Product
    try:
        with get_session() as session:
            session.add(Product(
                name=name.strip(), account_id=account_id,
                product_id_eduzz=eduzz_id or None,
                price=float(price) if price else 0,
                commission_percent=float(commission) if commission else 0,
            ))
        return no_update, False, False, (refresh or 0) + 1, "Produto criado!", True
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update, no_update, no_update


# Edit
@callback(
    Output("prod-edit-modal", "is_open"), Output("prod-edit-id", "data"),
    Output("prod-edit-name", "value"), Output("prod-edit-account", "options"), Output("prod-edit-account", "value"),
    Output("prod-edit-eduzz-id", "value"), Output("prod-edit-price", "value"),
    Output("prod-edit-commission", "value"), Output("prod-edit-active", "value"),
    Input("prod-edit-btn", "n_clicks"), Input("prod-edit-cancel", "n_clicks"),
    State("prod-grid", "selectedRows"),
    prevent_initial_call=True,
)
def toggle_edit(_e, _c, selected):
    if ctx.triggered_id == "prod-edit-cancel" or not selected:
        return False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    from app.database import get_session, Product
    with get_session() as session:
        p = session.get(Product, selected[0]["id"])
        if not p:
            return False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        return (True, p.id, p.name, _account_options(), p.account_id,
                p.product_id_eduzz or "", p.price, p.commission_percent, p.active)


@callback(
    Output("prod-edit-alert", "children"), Output("prod-edit-alert", "is_open"),
    Output("prod-edit-modal", "is_open", allow_duplicate=True),
    Output("prod-refresh", "data", allow_duplicate=True),
    Output("prod-toast", "children", allow_duplicate=True), Output("prod-toast", "is_open", allow_duplicate=True),
    Input("prod-edit-save", "n_clicks"),
    State("prod-edit-id", "data"), State("prod-edit-name", "value"), State("prod-edit-account", "value"),
    State("prod-edit-eduzz-id", "value"), State("prod-edit-price", "value"),
    State("prod-edit-commission", "value"), State("prod-edit-active", "value"),
    State("prod-refresh", "data"),
    prevent_initial_call=True,
)
def save_edit(_n, pid, name, account_id, eduzz_id, price, commission, active, refresh):
    if not name or not name.strip():
        return "Nome é obrigatório.", True, no_update, no_update, no_update, no_update
    from app.database import get_session, Product
    try:
        with get_session() as session:
            p = session.get(Product, pid)
            if not p:
                return "Produto não encontrado.", True, no_update, no_update, no_update, no_update
            p.name = name.strip()
            p.account_id = account_id
            p.product_id_eduzz = eduzz_id or None
            p.price = float(price) if price else 0
            p.commission_percent = float(commission) if commission else 0
            p.active = bool(active)
        return no_update, False, False, (refresh or 0) + 1, "Produto atualizado!", True
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update, no_update, no_update


# Delete
@callback(
    Output("prod-del-modal", "is_open"), Output("prod-del-id", "data"),
    Input("prod-del-btn", "n_clicks"), Input("prod-del-cancel", "n_clicks"),
    State("prod-grid", "selectedRows"),
    prevent_initial_call=True,
)
def toggle_delete(_d, _c, selected):
    if ctx.triggered_id == "prod-del-cancel" or not selected:
        return False, no_update
    return True, selected[0]["id"]


@callback(
    Output("prod-del-modal", "is_open", allow_duplicate=True),
    Output("prod-refresh", "data", allow_duplicate=True),
    Output("prod-toast", "children", allow_duplicate=True), Output("prod-toast", "is_open", allow_duplicate=True),
    Input("prod-del-confirm", "n_clicks"),
    State("prod-del-id", "data"), State("prod-refresh", "data"),
    prevent_initial_call=True,
)
def confirm_delete(_n, pid, refresh):
    if not pid:
        return False, no_update, no_update, no_update
    from app.database import get_session, Product
    with get_session() as session:
        p = session.get(Product, pid)
        if p:
            session.delete(p)
    return False, (refresh or 0) + 1, "Produto excluído.", True
