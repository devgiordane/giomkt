"""Eduzz account management page — OAuth2 multi-account."""

from datetime import date, timedelta

import dash
from dash import html, dcc, callback, Output, Input, State, no_update, ctx, clientside_callback
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

dash.register_page(__name__, path="/eduzz/accounts", name="Contas Eduzz")

layout = dbc.Container([
    dcc.Store(id="edz-refresh", data=0),
    dcc.Store(id="edz-edit-id"),
    dcc.Store(id="edz-del-id"),
    dcc.Store(id="edz-connect-url-store"),
    dcc.Location(id="edz-location", refresh=False),

    # Add modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Nova Conta Eduzz")),
        dbc.ModalBody([
            dbc.Alert(id="edz-add-alert", is_open=False, color="danger"),
            dbc.Alert(
                "Após criar a conta, clique em 'Conectar' para autenticar via Eduzz.",
                color="info", className="mb-3",
            ),
            dbc.Row([
                dbc.Col([dbc.Label("Nome da conta *"), dbc.Input(id="edz-add-name", placeholder="Ex: Conta Principal IRG")], className="mb-3"),
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="edz-add-cancel", color="secondary", className="me-2"),
            dbc.Button("Criar", id="edz-add-save", color="primary"),
        ]),
    ], id="edz-add-modal", is_open=False),

    # Edit modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Editar Conta")),
        dbc.ModalBody([
            dbc.Alert(id="edz-edit-alert", is_open=False, color="danger"),
            dbc.Row([
                dbc.Col([dbc.Label("Nome *"), dbc.Input(id="edz-edit-name")], md=6, className="mb-3"),
                dbc.Col([
                    dbc.Checkbox(id="edz-edit-active", label="Ativa", value=True),
                ], md=6, className="mb-3 d-flex align-items-end"),
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="edz-edit-cancel", color="secondary", className="me-2"),
            dbc.Button("Salvar", id="edz-edit-save", color="primary"),
        ]),
    ], id="edz-edit-modal", is_open=False),

    # Delete confirm
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Confirmar exclusão")),
        dbc.ModalBody("Tem certeza? Todos os produtos e vendas desta conta serão excluídos."),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="edz-del-cancel", color="secondary", className="me-2"),
            dbc.Button("Excluir", id="edz-del-confirm", color="danger"),
        ]),
    ], id="edz-del-modal", is_open=False),

    # Sync sales modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Sincronizar Vendas")),
        dbc.ModalBody([
            dbc.Alert(id="edz-sync-alert", is_open=False, color="danger"),
            dbc.Row([
                dbc.Col([dbc.Label("De"), dbc.Input(id="edz-sync-start", type="date",
                          value=(date.today().replace(day=1)).isoformat())], md=6, className="mb-3"),
                dbc.Col([dbc.Label("Até"), dbc.Input(id="edz-sync-end", type="date",
                          value=date.today().isoformat())], md=6, className="mb-3"),
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="edz-sync-cancel", color="secondary", className="me-2"),
            dbc.Button([html.I(className="bi bi-arrow-repeat me-1"), "Sincronizar"],
                       id="edz-sync-confirm", color="primary"),
        ]),
    ], id="edz-sync-modal", is_open=False),

    # Header
    dbc.Row([
        dbc.Col(html.H2([html.I(className="bi bi-shop me-2"), "Contas Eduzz"]), md=8),
        dbc.Col(
            dbc.Button([html.I(className="bi bi-plus-circle me-2"), "Nova Conta"],
                       id="edz-open-add", color="primary"),
            md=4, className="text-end",
        ),
    ], className="mb-4 mt-2 align-items-center"),

    html.Div(id="edz-table"),

    dbc.Toast(id="edz-toast", header="Contas Eduzz", is_open=False, dismissable=True, duration=4000,
              style={"position": "fixed", "bottom": "1rem", "right": "1rem", "zIndex": 9999}),
], fluid=True)


# ---------------------------------------------------------------------------
# Handle URL params on page load (connected=1 / error=...)
# ---------------------------------------------------------------------------

@callback(
    Output("edz-toast", "children", allow_duplicate=True),
    Output("edz-toast", "header", allow_duplicate=True),
    Output("edz-toast", "is_open", allow_duplicate=True),
    Output("edz-toast", "color", allow_duplicate=True),
    Output("edz-refresh", "data", allow_duplicate=True),
    Input("edz-location", "search"),
    State("edz-refresh", "data"),
    prevent_initial_call=True,
)
def handle_url_params(search, refresh):
    if not search:
        return no_update, no_update, no_update, no_update, no_update

    import urllib.parse
    params = dict(urllib.parse.parse_qsl(search.lstrip("?")))

    if params.get("connected") == "1":
        return "Conta conectada com sucesso!", "Eduzz", True, "success", (refresh or 0) + 1
    if params.get("error"):
        return f"Erro: {urllib.parse.unquote(params['error'])}", "Eduzz", True, "danger", no_update

    return no_update, no_update, no_update, no_update, no_update


# ---------------------------------------------------------------------------
# Load accounts table
# ---------------------------------------------------------------------------

@callback(
    Output("edz-table", "children"),
    Input("edz-refresh", "data"),
)
def load_accounts(_refresh):
    from app.database import get_session, EduzzAccount
    from app.services.eduzz import get_auth_url

    with get_session() as session:
        accounts = session.query(EduzzAccount).order_by(EduzzAccount.name).all()
        rows = []
        for a in accounts:
            connected = bool(a.access_token)
            status_badge = dbc.Badge(
                [html.I(className="bi bi-check-circle me-1"), "Conectado"] if connected
                else [html.I(className="bi bi-x-circle me-1"), "Não conectado"],
                color="success" if connected else "secondary",
            )
            auth_url = get_auth_url(a.id)
            rows.append(
                dbc.Card(dbc.CardBody(
                    dbc.Row([
                        dbc.Col([
                            html.H5(a.name, className="mb-1"),
                            html.Small(a.email or "—", className="text-muted"),
                        ], md=4),
                        dbc.Col(status_badge, md=2, className="d-flex align-items-center"),
                        dbc.Col([
                            html.A(
                                dbc.Button([html.I(className="bi bi-plug me-1"),
                                            "Reconectar" if connected else "Conectar"],
                                           color="primary" if not connected else "outline-secondary",
                                           size="sm", className="me-2"),
                                href=auth_url,
                            ),
                            dbc.Button([html.I(className="bi bi-arrow-down-circle me-1"), "Sincronizar Vendas"],
                                       id={"type": "edz-sync-sales-btn", "index": a.id},
                                       size="sm", color="info", className="me-2",
                                       disabled=not connected),
                            dbc.Button(html.I(className="bi bi-pencil"),
                                       id={"type": "edz-card-edit-btn", "index": a.id},
                                       size="sm", color="link", className="text-secondary me-1"),
                            dbc.Button(html.I(className="bi bi-trash"),
                                       id={"type": "edz-card-del-btn", "index": a.id},
                                       size="sm", color="link", className="text-danger"),
                        ], md=6, className="d-flex align-items-center justify-content-end"),
                    ], align="center")
                ), className="mb-2 kpi-card")
            )

    if not rows:
        return dbc.Alert([
            "Nenhuma conta cadastrada. Clique em ",
            html.Strong("Nova Conta"),
            " para começar.",
        ], color="info")

    return html.Div(rows)


# ---------------------------------------------------------------------------
# Add account
# ---------------------------------------------------------------------------

@callback(
    Output("edz-add-modal", "is_open"),
    Output("edz-add-name", "value"),
    Input("edz-open-add", "n_clicks"),
    Input("edz-add-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_add(_o, _c):
    if ctx.triggered_id == "edz-open-add":
        return True, ""
    return False, no_update


@callback(
    Output("edz-add-alert", "children"), Output("edz-add-alert", "is_open"),
    Output("edz-add-modal", "is_open", allow_duplicate=True),
    Output("edz-refresh", "data", allow_duplicate=True),
    Output("edz-toast", "children", allow_duplicate=True),
    Output("edz-toast", "is_open", allow_duplicate=True),
    Output("edz-toast", "color", allow_duplicate=True),
    Input("edz-add-save", "n_clicks"),
    State("edz-add-name", "value"),
    State("edz-refresh", "data"),
    prevent_initial_call=True,
)
def save_add(_n, name, refresh):
    if not name or not name.strip():
        return "Nome é obrigatório.", True, no_update, no_update, no_update, no_update, no_update
    from app.database import get_session, EduzzAccount
    try:
        with get_session() as session:
            session.add(EduzzAccount(name=name.strip()))
        return no_update, False, False, (refresh or 0) + 1, "Conta criada! Clique em 'Conectar' para autenticar.", True, "success"
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update, no_update, no_update, no_update


# ---------------------------------------------------------------------------
# Edit account
# ---------------------------------------------------------------------------

@callback(
    Output("edz-edit-modal", "is_open"), Output("edz-edit-id", "data"),
    Output("edz-edit-name", "value"), Output("edz-edit-active", "value"),
    Input({"type": "edz-card-edit-btn", "index": dash.ALL}, "n_clicks"),
    Input("edz-edit-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def open_edit(edit_clicks, _cancel):
    triggered = ctx.triggered_id
    if triggered == "edz-edit-cancel" or not any(c for c in edit_clicks if c):
        return False, no_update, no_update, no_update
    from app.database import get_session, EduzzAccount
    aid = triggered["index"]
    with get_session() as session:
        a = session.get(EduzzAccount, aid)
        if not a:
            return False, no_update, no_update, no_update
        return True, a.id, a.name, a.active


@callback(
    Output("edz-edit-alert", "children"), Output("edz-edit-alert", "is_open"),
    Output("edz-edit-modal", "is_open", allow_duplicate=True),
    Output("edz-refresh", "data", allow_duplicate=True),
    Output("edz-toast", "children", allow_duplicate=True),
    Output("edz-toast", "is_open", allow_duplicate=True),
    Output("edz-toast", "color", allow_duplicate=True),
    Input("edz-edit-save", "n_clicks"),
    State("edz-edit-id", "data"), State("edz-edit-name", "value"), State("edz-edit-active", "value"),
    State("edz-refresh", "data"),
    prevent_initial_call=True,
)
def save_edit(_n, aid, name, active, refresh):
    if not name or not name.strip():
        return "Nome é obrigatório.", True, no_update, no_update, no_update, no_update, no_update
    from app.database import get_session, EduzzAccount
    try:
        with get_session() as session:
            a = session.get(EduzzAccount, aid)
            if not a:
                return "Conta não encontrada.", True, no_update, no_update, no_update, no_update, no_update
            a.name = name.strip()
            a.active = bool(active)
        return no_update, False, False, (refresh or 0) + 1, "Conta atualizada!", True, "success"
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update, no_update, no_update, no_update


# ---------------------------------------------------------------------------
# Delete account
# ---------------------------------------------------------------------------

@callback(
    Output("edz-del-modal", "is_open"), Output("edz-del-id", "data"),
    Input({"type": "edz-card-del-btn", "index": dash.ALL}, "n_clicks"),
    Input("edz-del-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def open_delete(del_clicks, _cancel):
    triggered = ctx.triggered_id
    if triggered == "edz-del-cancel" or not any(c for c in del_clicks if c):
        return False, no_update
    return True, triggered["index"]


@callback(
    Output("edz-del-modal", "is_open", allow_duplicate=True),
    Output("edz-refresh", "data", allow_duplicate=True),
    Output("edz-toast", "children", allow_duplicate=True),
    Output("edz-toast", "is_open", allow_duplicate=True),
    Output("edz-toast", "color", allow_duplicate=True),
    Input("edz-del-confirm", "n_clicks"),
    State("edz-del-id", "data"), State("edz-refresh", "data"),
    prevent_initial_call=True,
)
def confirm_delete(_n, aid, refresh):
    if not aid:
        return False, no_update, no_update, no_update, no_update
    from app.database import get_session, EduzzAccount
    with get_session() as session:
        a = session.get(EduzzAccount, aid)
        if a:
            session.delete(a)
    return False, (refresh or 0) + 1, "Conta excluída.", True, "warning"


# ---------------------------------------------------------------------------
# Sync sales modal
# ---------------------------------------------------------------------------

@callback(
    Output("edz-sync-modal", "is_open"),
    Output("edz-edit-id", "data", allow_duplicate=True),
    Input({"type": "edz-sync-sales-btn", "index": dash.ALL}, "n_clicks"),
    Input("edz-sync-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def open_sync_modal(sync_clicks, _cancel):
    triggered = ctx.triggered_id
    if triggered == "edz-sync-cancel" or not any(c for c in sync_clicks if c):
        return False, no_update
    return True, triggered["index"]


@callback(
    Output("edz-sync-alert", "children"), Output("edz-sync-alert", "is_open"),
    Output("edz-sync-modal", "is_open", allow_duplicate=True),
    Output("edz-toast", "children", allow_duplicate=True),
    Output("edz-toast", "is_open", allow_duplicate=True),
    Output("edz-toast", "color", allow_duplicate=True),
    Input("edz-sync-confirm", "n_clicks"),
    State("edz-edit-id", "data"),
    State("edz-sync-start", "value"),
    State("edz-sync-end", "value"),
    prevent_initial_call=True,
)
def do_sync(_n, account_id, start_str, end_str):
    if not account_id:
        return "Nenhuma conta selecionada.", True, no_update, no_update, no_update, no_update

    from app.services.eduzz import sync_sales

    try:
        start = date.fromisoformat(start_str) if start_str else date.today().replace(day=1)
        end = date.fromisoformat(end_str) if end_str else date.today()
    except ValueError:
        return "Datas inválidas.", True, no_update, no_update, no_update, no_update

    result = sync_sales(int(account_id), start, end)

    if "error" in result:
        return result["error"], True, no_update, no_update, no_update, no_update

    msg = f"Sincronizado: {result['created']} novas vendas, {result['skipped']} ignoradas."
    return no_update, False, False, msg, True, "success"
