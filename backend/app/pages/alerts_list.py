"""Triggered alerts list page."""

import dash
from dash import html, dcc, callback, Output, Input, State, no_update
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

dash.register_page(__name__, path="/alerts", name="Alertas")

layout = dbc.Container(
    [
        dcc.Store(id="alerts-refresh-store", data=0),
        dbc.Row(
            [
                dbc.Col(html.H2("Alertas"), md=8),
                dbc.Col(
                    dbc.Button(
                        [html.I(className="bi bi-arrow-clockwise me-2"), "Verificar Agora"],
                        id="alerts-check-btn",
                        color="warning",
                        className="float-end",
                    ),
                    md=4,
                ),
            ],
            className="mb-4 mt-2 align-items-center",
        ),
        dbc.Alert(id="alerts-check-result", is_open=False, dismissable=True, className="mb-3"),
        dbc.Row(
            dbc.Col(
                dag.AgGrid(
                    id="alerts-grid",
                    columnDefs=[
                        {"field": "id", "headerName": "ID", "width": 80},
                        {"field": "client", "headerName": "Cliente", "flex": 2},
                        {"field": "message", "headerName": "Mensagem", "flex": 4},
                        {"field": "triggered_at", "headerName": "Disparado em", "flex": 1},
                        {"field": "resolved", "headerName": "Resolvido", "width": 120},
                    ],
                    rowData=[],
                    defaultColDef={"resizable": True, "sortable": True, "filter": True},
                    dashGridOptions={"pagination": True, "paginationPageSize": 25},
                    style={"height": "450px"},
                    className="ag-theme-alpine-dark",
                )
            )
        ),
        dcc.Interval(id="alerts-interval", interval=30_000, n_intervals=0),
    ],
    fluid=True,
)


@callback(
    Output("alerts-grid", "rowData"),
    Input("alerts-interval", "n_intervals"),
    Input("alerts-refresh-store", "data"),
)
def load_alerts(_interval, _refresh):
    from app.database import get_session, Alert, Client

    with get_session() as session:
        alerts = session.query(Alert).order_by(Alert.triggered_at.desc()).limit(200).all()
        client_map = {c.id: c.name for c in session.query(Client).all()}

        rows = [
            {
                "id": a.id,
                "client": client_map.get(a.client_id, f"#{a.client_id}"),
                "message": a.message,
                "triggered_at": a.triggered_at.strftime("%d/%m/%Y %H:%M") if a.triggered_at else "",
                "resolved": "Sim" if a.resolved else "Não",
            }
            for a in alerts
        ]
    return rows


@callback(
    Output("alerts-check-result", "children"),
    Output("alerts-check-result", "color"),
    Output("alerts-check-result", "is_open"),
    Output("alerts-refresh-store", "data"),
    Input("alerts-check-btn", "n_clicks"),
    State("alerts-refresh-store", "data"),
    prevent_initial_call=True,
)
def run_check(_n, refresh):
    from app.services.alerts import check_budget_alerts

    try:
        triggered = check_budget_alerts()
        if triggered:
            msg = f"{len(triggered)} alerta(s) disparado(s)."
            color = "warning"
        else:
            msg = "Nenhum alerta disparado."
            color = "success"
        return msg, color, True, (refresh or 0) + 1
    except Exception as exc:
        return f"Erro: {exc}", "danger", True, no_update


@callback(
    Output("alerts-refresh-store", "data", allow_duplicate=True),
    Input("alerts-grid", "cellRendererData"),
    State("alerts-refresh-store", "data"),
    prevent_initial_call=True,
)
def resolve_alert(cell_data, refresh):
    if not cell_data or cell_data.get("value") != "resolve":
        return no_update

    row_id = cell_data.get("rowId")
    if row_id is None:
        return no_update

    from app.database import get_session, Alert

    with get_session() as session:
        alert = session.get(Alert, int(row_id))
        if alert:
            alert.resolved = True

    return (refresh or 0) + 1
