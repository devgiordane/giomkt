"""Eduzz Webhook subscription management page."""

import json

import dash
from dash import html, dcc, callback, Output, Input, State, no_update, ctx
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

dash.register_page(__name__, path="/webhooks", name="Webhooks")

# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

def _status_badge(status: str):
    color = "success" if status == "active" else "secondary"
    return dbc.Badge(status, color=color, className="ms-1")


def _accounts_options():
    from app.database import get_session, EduzzAccount
    with get_session() as session:
        accounts = session.query(EduzzAccount).filter_by(active=True).all()
        return [{"label": a.name, "value": a.id} for a in accounts]


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

layout = dbc.Container([
    dcc.Store(id="wh-refresh", data=0),
    dcc.Store(id="wh-edit-id"),   # local DB id being edited
    dcc.Store(id="wh-del-id"),    # local DB id to delete
    dcc.Interval(id="wh-interval", interval=60_000, n_intervals=0),

    # ── Create modal ──────────────────────────────────────────────────────
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Nova Inscrição de Webhook")),
        dbc.ModalBody([
            dbc.Alert(id="wh-add-alert", is_open=False, color="danger"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Conta Eduzz *"),
                    dcc.Dropdown(id="wh-add-account", placeholder="Selecione a conta..."),
                ], md=6, className="mb-3"),
                dbc.Col([
                    dbc.Label("Nome *"),
                    dbc.Input(id="wh-add-name", placeholder="Ex: Vendas - Produto A"),
                ], md=6, className="mb-3"),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("URL de destino *"),
                    dbc.Input(id="wh-add-url", placeholder="https://..."),
                ], className="mb-3"),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Eventos (selecione a conta para carregar)"),
                    dcc.Dropdown(
                        id="wh-add-events",
                        multi=True,
                        placeholder="Selecione os eventos...",
                    ),
                ], className="mb-3"),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Filtros (opcional)"),
                    dbc.Textarea(
                        id="wh-add-filters",
                        placeholder='JSON, ex: [{"metadata":"productId","values":["123"]}]',
                        rows=3,
                    ),
                    dbc.FormText("Deixe em branco para receber todos os eventos."),
                ], className="mb-3"),
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="wh-add-cancel", color="secondary", className="me-2"),
            dbc.Button("Criar", id="wh-add-save", color="primary"),
        ]),
    ], id="wh-add-modal", is_open=False, size="lg"),

    # ── Edit modal ────────────────────────────────────────────────────────
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Editar Inscrição")),
        dbc.ModalBody([
            dbc.Alert(id="wh-edit-alert", is_open=False, color="danger"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Nome *"),
                    dbc.Input(id="wh-edit-name"),
                ], md=6, className="mb-3"),
                dbc.Col([
                    dbc.Label("URL de destino *"),
                    dbc.Input(id="wh-edit-url"),
                ], md=6, className="mb-3"),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Eventos"),
                    dcc.Dropdown(id="wh-edit-events", multi=True),
                ], className="mb-3"),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Filtros (JSON)"),
                    dbc.Textarea(id="wh-edit-filters", rows=3),
                ], className="mb-3"),
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="wh-edit-cancel", color="secondary", className="me-2"),
            dbc.Button("Salvar", id="wh-edit-save", color="primary"),
        ]),
    ], id="wh-edit-modal", is_open=False, size="lg"),

    # ── Delete confirm modal ──────────────────────────────────────────────
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Confirmar exclusão")),
        dbc.ModalBody("Tem certeza que deseja excluir esta inscrição? Esta ação também a remove da Eduzz."),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="wh-del-cancel", color="secondary", className="me-2"),
            dbc.Button("Excluir", id="wh-del-confirm", color="danger"),
        ]),
    ], id="wh-del-modal", is_open=False),

    # ── Test modal ────────────────────────────────────────────────────────
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Testar Webhook")),
        dbc.ModalBody([
            dbc.Alert(id="wh-test-alert", is_open=False),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Evento de teste"),
                    dbc.Input(id="wh-test-event", placeholder="Ex: nutror.lesson_watched"),
                ], className="mb-3"),
            ]),
            html.Div(id="wh-test-result"),
        ]),
        dbc.ModalFooter([
            dbc.Button("Fechar", id="wh-test-cancel", color="secondary", className="me-2"),
            dbc.Button("Enviar teste", id="wh-test-send", color="primary"),
        ]),
    ], id="wh-test-modal", is_open=False),

    # ── Page header ───────────────────────────────────────────────────────
    dbc.Row([
        dbc.Col(html.H3([html.I(className="bi bi-plugin me-2"), "Webhooks"]), width="auto"),
        dbc.Col(
            dbc.Button([html.I(className="bi bi-plus-lg me-1"), "Nova inscrição"],
                       id="wh-add-btn", color="primary", size="sm"),
            className="ms-auto d-flex align-items-center",
        ),
    ], className="mb-3 mt-1 align-items-center"),

    dbc.Alert(id="wh-page-alert", is_open=False, dismissable=True, className="mb-3"),

    # ── Subscriptions table ───────────────────────────────────────────────
    dbc.Card([
        dbc.CardHeader([html.I(className="bi bi-list-ul me-2"), "Inscrições"]),
        dbc.CardBody([
            html.Div(id="wh-subscriptions-table"),
        ]),
    ], className="mb-4"),

    # ── Recent events ─────────────────────────────────────────────────────
    dbc.Card([
        dbc.CardHeader([html.I(className="bi bi-clock-history me-2"), "Eventos recebidos (últimos 100)"]),
        dbc.CardBody([
            dag.AgGrid(
                id="wh-events-grid",
                columnDefs=[
                    {"field": "id", "headerName": "ID", "width": 70},
                    {"field": "received_at", "headerName": "Recebido em", "width": 180},
                    {"field": "event_type", "headerName": "Evento", "flex": 1},
                    {"field": "subscription_name", "headerName": "Inscrição", "flex": 1},
                    {"field": "processed", "headerName": "Processado", "width": 120,
                     "cellRenderer": "agCheckboxCellRenderer"},
                ],
                rowData=[],
                defaultColDef={"resizable": True, "sortable": True, "filter": True},
                style={"height": "300px"},
                className="ag-theme-alpine-dark",
            ),
        ]),
    ]),
], fluid=True)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

# ── Open add modal ───────────────────────────────────────────────────────────
@callback(
    Output("wh-add-modal", "is_open"),
    Output("wh-add-account", "options"),
    Output("wh-add-name", "value"),
    Output("wh-add-url", "value"),
    Output("wh-add-events", "value"),
    Output("wh-add-filters", "value"),
    Output("wh-add-alert", "is_open"),
    Input("wh-add-btn", "n_clicks"),
    Input("wh-add-cancel", "n_clicks"),
    Input("wh-add-save", "n_clicks"),
    prevent_default_on_submit=False,
    prevent_initial_call=True,
)
def _toggle_add_modal(open_clicks, cancel_clicks, save_clicks):
    trigger = ctx.triggered_id
    if trigger == "wh-add-btn":
        return True, _accounts_options(), "", "", [], "", False
    return False, no_update, no_update, no_update, no_update, no_update, False


# ── Load events for selected account ─────────────────────────────────────────
@callback(
    Output("wh-add-events", "options"),
    Input("wh-add-account", "value"),
    prevent_initial_call=True,
)
def _load_events_for_account(account_id):
    if not account_id:
        return []
    from app.services.eduzz_webhooks import list_origins
    result = list_origins(account_id)
    if "error" in result:
        return []
    options = []
    for origin in result.get("items", []):
        for evt in origin.get("events", []):
            name = evt.get("name", "")
            desc = evt.get("description", name)
            options.append({"label": f"{name} — {desc}", "value": name})
    return options


# ── Save new subscription ────────────────────────────────────────────────────
@callback(
    Output("wh-add-modal", "is_open", allow_duplicate=True),
    Output("wh-add-alert", "children"),
    Output("wh-add-alert", "is_open", allow_duplicate=True),
    Output("wh-refresh", "data", allow_duplicate=True),
    Input("wh-add-save", "n_clicks"),
    State("wh-add-account", "value"),
    State("wh-add-name", "value"),
    State("wh-add-url", "value"),
    State("wh-add-events", "value"),
    State("wh-add-filters", "value"),
    State("wh-refresh", "data"),
    prevent_initial_call=True,
)
def _save_new_subscription(n, account_id, name, url, events, filters_raw, refresh):
    if not n:
        return no_update, no_update, no_update, no_update
    if not account_id:
        return no_update, "Selecione uma conta Eduzz.", True, no_update
    if not name or not name.strip():
        return no_update, "Informe um nome.", True, no_update
    if not url or not url.strip():
        return no_update, "Informe a URL de destino.", True, no_update
    if not events:
        return no_update, "Selecione pelo menos um evento.", True, no_update

    filters = None
    if filters_raw and filters_raw.strip():
        try:
            filters = json.loads(filters_raw)
        except Exception:
            return no_update, "Filtros com JSON inválido.", True, no_update

    from app.services.eduzz_webhooks import create_subscription, sync_subscription_to_db
    result = create_subscription(account_id, name.strip(), url.strip(), events, filters)
    if "error" in result:
        return no_update, result["error"], True, no_update

    sync_subscription_to_db(account_id, result)
    return False, "", False, (refresh or 0) + 1


# ── Subscriptions table ───────────────────────────────────────────────────────
@callback(
    Output("wh-subscriptions-table", "children"),
    Input("wh-refresh", "data"),
    Input("wh-interval", "n_intervals"),
)
def _render_subscriptions(refresh, _intervals):
    from app.database import get_session, WebhookSubscription, EduzzAccount
    with get_session() as session:
        subs = (
            session.query(WebhookSubscription)
            .join(EduzzAccount)
            .order_by(WebhookSubscription.created_at.desc())
            .all()
        )
        if not subs:
            return dbc.Alert("Nenhuma inscrição cadastrada. Clique em 'Nova inscrição' para começar.", color="info")

        rows = []
        for s in subs:
            events_list = json.loads(s.events or "[]")
            events_badges = [dbc.Badge(e, color="dark", className="me-1") for e in events_list[:4]]
            if len(events_list) > 4:
                events_badges.append(dbc.Badge(f"+{len(events_list) - 4}", color="secondary"))

            status_color = "success" if s.status == "active" else "secondary"
            rows.append(
                html.Tr([
                    html.Td(s.id),
                    html.Td(s.account.name if s.account else "—"),
                    html.Td(s.name),
                    html.Td(html.Code(s.url, style={"fontSize": "0.8em"})),
                    html.Td(html.Span(events_badges)),
                    html.Td(dbc.Badge(s.status, color=status_color)),
                    html.Td([
                        dbc.Button(
                            html.I(className="bi bi-pencil"),
                            id={"type": "wh-edit-btn", "index": s.id},
                            color="outline-secondary", size="sm", className="me-1",
                        ),
                        dbc.Button(
                            html.I(className="bi bi-play-fill" if s.status != "active" else "bi bi-pause-fill"),
                            id={"type": "wh-toggle-btn", "index": s.id},
                            color="outline-warning", size="sm", className="me-1",
                            title="Ativar" if s.status != "active" else "Desativar",
                        ),
                        dbc.Button(
                            html.I(className="bi bi-send"),
                            id={"type": "wh-test-btn", "index": s.id},
                            color="outline-info", size="sm", className="me-1",
                            title="Testar",
                        ),
                        dbc.Button(
                            html.I(className="bi bi-trash"),
                            id={"type": "wh-del-btn", "index": s.id},
                            color="outline-danger", size="sm",
                        ),
                    ]),
                ])
            )

        return dbc.Table(
            [
                html.Thead(html.Tr([
                    html.Th("ID"), html.Th("Conta"), html.Th("Nome"),
                    html.Th("URL"), html.Th("Eventos"), html.Th("Status"), html.Th("Ações"),
                ])),
                html.Tbody(rows),
            ],
            bordered=True, hover=True, responsive=True, size="sm",
        )


# ── Toggle status ─────────────────────────────────────────────────────────────
@callback(
    Output("wh-refresh", "data", allow_duplicate=True),
    Output("wh-page-alert", "children", allow_duplicate=True),
    Output("wh-page-alert", "is_open", allow_duplicate=True),
    Output("wh-page-alert", "color", allow_duplicate=True),
    Input({"type": "wh-toggle-btn", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def _toggle_status(n_clicks_list):
    if not any(n_clicks_list):
        return no_update, no_update, no_update, no_update
    triggered = ctx.triggered_id
    if not triggered:
        return no_update, no_update, no_update, no_update
    sub_id = triggered["index"]

    from app.database import get_session, WebhookSubscription
    from app.services.eduzz_webhooks import set_subscription_status
    with get_session() as session:
        sub = session.get(WebhookSubscription, sub_id)
        if not sub:
            return no_update, "Inscrição não encontrada.", True, "danger"
        new_status = "active" if sub.status != "active" else "disabled"
        result = set_subscription_status(sub.account_id, sub.eduzz_subscription_id, new_status)
        if "error" in result:
            return no_update, result["error"], True, "danger"
        sub.status = new_status

    from dash import callback_context
    return 1, f"Status alterado para '{new_status}'.", True, "success"


# ── Open edit modal ───────────────────────────────────────────────────────────
@callback(
    Output("wh-edit-modal", "is_open"),
    Output("wh-edit-id", "data"),
    Output("wh-edit-name", "value"),
    Output("wh-edit-url", "value"),
    Output("wh-edit-events", "options"),
    Output("wh-edit-events", "value"),
    Output("wh-edit-filters", "value"),
    Input({"type": "wh-edit-btn", "index": dash.ALL}, "n_clicks"),
    Input("wh-edit-cancel", "n_clicks"),
    Input("wh-edit-save", "n_clicks"),
    prevent_initial_call=True,
)
def _open_edit_modal(edit_clicks, cancel, save):
    trigger = ctx.triggered_id
    if trigger in ("wh-edit-cancel", "wh-edit-save"):
        return False, no_update, no_update, no_update, no_update, no_update, no_update

    if not trigger or not any(edit_clicks):
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update

    sub_id = trigger["index"]
    from app.database import get_session, WebhookSubscription
    from app.services.eduzz_webhooks import list_origins
    with get_session() as session:
        sub = session.get(WebhookSubscription, sub_id)
        if not sub:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update
        events_val = json.loads(sub.events or "[]")
        account_id = sub.account_id

    origins = list_origins(account_id)
    event_options = []
    for origin in origins.get("items", []):
        for evt in origin.get("events", []):
            n = evt.get("name", "")
            d = evt.get("description", n)
            event_options.append({"label": f"{n} — {d}", "value": n})
    # Ensure currently selected events appear even if not in origins list
    for e in events_val:
        if not any(o["value"] == e for o in event_options):
            event_options.append({"label": e, "value": e})

    return True, sub_id, sub.name, sub.url, event_options, events_val, ""


# ── Save edit ────────────────────────────────────────────────────────────────
@callback(
    Output("wh-edit-modal", "is_open", allow_duplicate=True),
    Output("wh-edit-alert", "children"),
    Output("wh-edit-alert", "is_open"),
    Output("wh-refresh", "data", allow_duplicate=True),
    Input("wh-edit-save", "n_clicks"),
    State("wh-edit-id", "data"),
    State("wh-edit-name", "value"),
    State("wh-edit-url", "value"),
    State("wh-edit-events", "value"),
    State("wh-edit-filters", "value"),
    State("wh-refresh", "data"),
    prevent_initial_call=True,
)
def _save_edit(n, sub_id, name, url, events, filters_raw, refresh):
    if not n:
        return no_update, no_update, no_update, no_update
    if not name or not url or not events:
        return no_update, "Preencha todos os campos obrigatórios.", True, no_update

    filters = None
    if filters_raw and filters_raw.strip():
        try:
            filters = json.loads(filters_raw)
        except Exception:
            return no_update, "Filtros com JSON inválido.", True, no_update

    from app.database import get_session, WebhookSubscription
    from app.services.eduzz_webhooks import update_subscription
    with get_session() as session:
        sub = session.get(WebhookSubscription, sub_id)
        if not sub:
            return no_update, "Inscrição não encontrada.", True, no_update
        result = update_subscription(sub.account_id, sub.eduzz_subscription_id, name, url, events, filters)
        if "error" in result:
            return no_update, result["error"], True, no_update
        sub.name = name
        sub.url = url
        sub.events = json.dumps(events)

    return False, "", False, (refresh or 0) + 1


# ── Open delete modal ─────────────────────────────────────────────────────────
@callback(
    Output("wh-del-modal", "is_open"),
    Output("wh-del-id", "data"),
    Input({"type": "wh-del-btn", "index": dash.ALL}, "n_clicks"),
    Input("wh-del-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def _open_del_modal(del_clicks, cancel):
    trigger = ctx.triggered_id
    if trigger == "wh-del-cancel" or not any(del_clicks):
        return False, no_update
    return True, trigger["index"]


# ── Confirm delete ────────────────────────────────────────────────────────────
@callback(
    Output("wh-del-modal", "is_open", allow_duplicate=True),
    Output("wh-refresh", "data", allow_duplicate=True),
    Output("wh-page-alert", "children", allow_duplicate=True),
    Output("wh-page-alert", "is_open", allow_duplicate=True),
    Output("wh-page-alert", "color", allow_duplicate=True),
    Input("wh-del-confirm", "n_clicks"),
    State("wh-del-id", "data"),
    State("wh-refresh", "data"),
    prevent_initial_call=True,
)
def _confirm_delete(n, sub_id, refresh):
    if not n:
        return no_update, no_update, no_update, no_update, no_update
    from app.database import get_session, WebhookSubscription
    from app.services.eduzz_webhooks import delete_subscription
    with get_session() as session:
        sub = session.get(WebhookSubscription, sub_id)
        if not sub:
            return False, no_update, "Inscrição não encontrada.", True, "danger"
        eduzz_id = sub.eduzz_subscription_id
        account_id = sub.account_id
        if eduzz_id:
            result = delete_subscription(account_id, eduzz_id)
            if "error" in result:
                return False, no_update, result["error"], True, "danger"
        session.delete(sub)

    return False, (refresh or 0) + 1, "Inscrição excluída.", True, "success"


# ── Open test modal ───────────────────────────────────────────────────────────
@callback(
    Output("wh-test-modal", "is_open"),
    Output("wh-edit-id", "data", allow_duplicate=True),
    Output("wh-test-event", "value"),
    Output("wh-test-result", "children"),
    Input({"type": "wh-test-btn", "index": dash.ALL}, "n_clicks"),
    Input("wh-test-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def _open_test_modal(test_clicks, cancel):
    trigger = ctx.triggered_id
    if trigger == "wh-test-cancel" or not any(test_clicks):
        return False, no_update, no_update, no_update
    sub_id = trigger["index"]
    return True, sub_id, "", html.Div()


# ── Send test ─────────────────────────────────────────────────────────────────
@callback(
    Output("wh-test-alert", "children"),
    Output("wh-test-alert", "is_open"),
    Output("wh-test-alert", "color"),
    Output("wh-test-result", "children", allow_duplicate=True),
    Input("wh-test-send", "n_clicks"),
    State("wh-edit-id", "data"),
    State("wh-test-event", "value"),
    prevent_initial_call=True,
)
def _send_test(n, sub_id, event_name):
    if not n:
        return no_update, no_update, no_update, no_update
    if not event_name or not event_name.strip():
        return "Informe o nome do evento.", True, "warning", no_update

    from app.database import get_session, WebhookSubscription
    from app.services.eduzz_webhooks import send_test
    with get_session() as session:
        sub = session.get(WebhookSubscription, sub_id)
        if not sub:
            return "Inscrição não encontrada.", True, "danger", no_update
        result = send_test(sub.account_id, sub.eduzz_subscription_id, event_name.strip())

    if "error" in result:
        return result["error"], True, "danger", no_update

    status_code = result.get("statusCode", "—")
    time_taken = result.get("timeTaken", "—")
    body = result.get("body", "")
    result_card = dbc.Card(dbc.CardBody([
        html.P([html.Strong("HTTP Status: "), str(status_code)]),
        html.P([html.Strong("Latência: "), f"{time_taken} ms"]),
        html.P(html.Strong("Resposta:")),
        html.Pre(body, style={"maxHeight": "150px", "overflow": "auto", "fontSize": "0.8em"}),
    ]), className="mt-2")
    return "Teste enviado com sucesso!", True, "success", result_card


# ── Events grid ───────────────────────────────────────────────────────────────
@callback(
    Output("wh-events-grid", "rowData"),
    Input("wh-refresh", "data"),
    Input("wh-interval", "n_intervals"),
)
def _load_events(refresh, _intervals):
    from app.database import get_session, WebhookEvent, WebhookSubscription
    with get_session() as session:
        events = (
            session.query(WebhookEvent)
            .outerjoin(WebhookSubscription)
            .order_by(WebhookEvent.received_at.desc())
            .limit(100)
            .all()
        )
        rows = []
        for e in events:
            rows.append({
                "id": e.id,
                "received_at": e.received_at.strftime("%d/%m/%Y %H:%M:%S") if e.received_at else "—",
                "event_type": e.event_type,
                "subscription_name": e.subscription.name if e.subscription else "—",
                "processed": e.processed,
            })
        return rows
