"""Alert rules management page."""

import dash
from dash import html, dcc, callback, Output, Input, State, no_update
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

dash.register_page(__name__, path="/alerts/rules", name="Regras de Alerta")

# ---------------------------------------------------------------------------
# Modal
# ---------------------------------------------------------------------------

rule_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Regra de Alerta")),
        dbc.ModalBody(
            [
                dbc.Alert(id="ar-modal-alert", is_open=False, color="danger"),
                dcc.Store(id="ar-editing-id-store"),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Cliente *"),
                                dcc.Dropdown(id="ar-modal-client", placeholder="Selecione um cliente"),
                            ],
                            className="mb-3",
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Tipo de Regra *"),
                                dbc.Select(
                                    id="ar-modal-rule-type",
                                    options=[
                                        {"label": "Orçamento Diário", "value": "daily_budget"},
                                        {"label": "Orçamento Mensal", "value": "monthly_budget"},
                                    ],
                                    value="daily_budget",
                                ),
                            ],
                            md=6,
                            className="mb-3",
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Threshold (%) *"),
                                dbc.Input(id="ar-modal-threshold", type="number", min=1, max=200, value=80),
                            ],
                            md=6,
                            className="mb-3",
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Checklist(
                                options=[{"label": "Notificar via WhatsApp", "value": "yes"}],
                                value=[],
                                id="ar-modal-notify-wa",
                                inline=True,
                            ),
                            className="mb-3",
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Checklist(
                                options=[{"label": "Regra Ativa", "value": "yes"}],
                                value=["yes"],
                                id="ar-modal-active",
                                inline=True,
                            ),
                            className="mb-3",
                        )
                    ]
                ),
            ]
        ),
        dbc.ModalFooter(
            [
                dbc.Button("Cancelar", id="ar-modal-cancel", color="secondary", className="me-2"),
                dbc.Button("Salvar", id="ar-modal-save", color="primary"),
            ]
        ),
    ],
    id="ar-modal",
    is_open=False,
)

layout = dbc.Container(
    [
        dcc.Store(id="ar-refresh-store", data=0),
        rule_modal,

        dbc.Row(
            [
                dbc.Col(html.H2("Regras de Alerta"), md=8),
                dbc.Col(
                    dbc.Button(
                        [html.I(className="bi bi-plus-circle me-2"), "Nova Regra"],
                        id="ar-open-modal-btn",
                        color="primary",
                        className="float-end",
                    ),
                    md=4,
                ),
            ],
            className="mb-4 mt-2 align-items-center",
        ),

        dbc.Row(
            dbc.Col(
                dag.AgGrid(
                    id="ar-grid",
                    columnDefs=[
                        {"field": "id", "headerName": "ID", "width": 80},
                        {"field": "client", "headerName": "Cliente", "flex": 2},
                        {"field": "rule_type", "headerName": "Tipo", "flex": 1},
                        {"field": "threshold", "headerName": "Threshold (%)", "width": 140},
                        {"field": "notify_whatsapp", "headerName": "WhatsApp", "width": 120},
                        {"field": "active", "headerName": "Ativo", "width": 100},
                    ],
                    rowData=[],
                    defaultColDef={"resizable": True, "sortable": True, "filter": True},
                    dashGridOptions={"pagination": True, "paginationPageSize": 25},
                    style={"height": "450px"},
                    className="ag-theme-alpine-dark",
                )
            )
        ),
        dcc.Interval(id="ar-interval", interval=60_000, n_intervals=0),
    ],
    fluid=True,
)


@callback(
    Output("ar-grid", "rowData"),
    Input("ar-interval", "n_intervals"),
    Input("ar-refresh-store", "data"),
)
def load_rules(_interval, _refresh):
    from app.database import get_session, AlertRule, Client

    with get_session() as session:
        rules = session.query(AlertRule).order_by(AlertRule.id.desc()).all()
        client_map = {c.id: c.name for c in session.query(Client).all()}

        rows = [
            {
                "id": r.id,
                "client": client_map.get(r.client_id, f"#{r.client_id}"),
                "rule_type": r.rule_type,
                "threshold": r.threshold,
                "notify_whatsapp": "Sim" if r.notify_whatsapp else "Não",
                "active": "Sim" if r.active else "Não",
            }
            for r in rules
        ]
    return rows


@callback(
    Output("ar-modal", "is_open"),
    Output("ar-modal-client", "options"),
    Input("ar-open-modal-btn", "n_clicks"),
    Input("ar-modal-cancel", "n_clicks"),
    State("ar-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_modal(_open, _cancel, is_open):
    from app.database import get_session, Client

    if not is_open:
        with get_session() as session:
            clients = session.query(Client).all()
            options = [{"label": c.name, "value": c.id} for c in clients]
    else:
        options = no_update

    return not is_open, options


@callback(
    Output("ar-modal-alert", "children"),
    Output("ar-modal-alert", "is_open"),
    Output("ar-modal", "is_open", allow_duplicate=True),
    Output("ar-refresh-store", "data"),
    Input("ar-modal-save", "n_clicks"),
    State("ar-modal-client", "value"),
    State("ar-modal-rule-type", "value"),
    State("ar-modal-threshold", "value"),
    State("ar-modal-notify-wa", "value"),
    State("ar-modal-active", "value"),
    State("ar-refresh-store", "data"),
    prevent_initial_call=True,
)
def save_rule(_n, client_id, rule_type, threshold, notify_wa, active_val, refresh):
    if not client_id:
        return "Cliente é obrigatório.", True, no_update, no_update
    if not threshold:
        return "Threshold é obrigatório.", True, no_update, no_update

    from app.database import get_session, AlertRule

    try:
        with get_session() as session:
            rule = AlertRule(
                client_id=int(client_id),
                rule_type=rule_type,
                threshold=float(threshold),
                notify_whatsapp="yes" in (notify_wa or []),
                active="yes" in (active_val or []),
            )
            session.add(rule)
        return no_update, False, False, (refresh or 0) + 1
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update


@callback(
    Output("ar-refresh-store", "data", allow_duplicate=True),
    Input("ar-grid", "cellRendererData"),
    State("ar-refresh-store", "data"),
    prevent_initial_call=True,
)
def delete_rule(cell_data, refresh):
    if not cell_data or cell_data.get("value") != "delete":
        return no_update

    row_id = cell_data.get("rowId")
    if row_id is None:
        return no_update

    from app.database import get_session, AlertRule

    with get_session() as session:
        rule = session.get(AlertRule, int(row_id))
        if rule:
            session.delete(rule)

    return (refresh or 0) + 1
