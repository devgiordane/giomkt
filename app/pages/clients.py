"""Clients list page."""

import dash
from dash import html, dcc, callback, Output, Input, State, no_update
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

dash.register_page(__name__, path="/clients", name="Clientes")

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

delete_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Confirmar exclusão")),
        dbc.ModalBody("Tem certeza que deseja excluir este cliente?"),
        dbc.ModalFooter(
            [
                dbc.Button("Cancelar", id="clients-cancel-delete", className="me-2", color="secondary"),
                dbc.Button("Excluir", id="clients-confirm-delete", color="danger"),
            ]
        ),
    ],
    id="clients-delete-modal",
    is_open=False,
)

layout = dbc.Container(
    [
        dcc.Store(id="clients-delete-id-store"),
        dcc.Location(id="clients-location", refresh=True),
        delete_modal,
        dbc.Row(
            [
                dbc.Col(html.H2("Clientes"), md=8),
                dbc.Col(
                    dbc.Button(
                        [html.I(className="bi bi-plus-circle me-2"), "Novo Cliente"],
                        href="/clients/new",
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
                    id="clients-grid",
                    columnDefs=[
                        {"field": "id", "headerName": "ID", "width": 80},
                        {"field": "name", "headerName": "Nome", "flex": 2},
                        {"field": "email", "headerName": "Email", "flex": 2},
                        {"field": "phone", "headerName": "Telefone", "flex": 1},
                        {"field": "status", "headerName": "Status", "width": 110},
                        {"field": "created_at", "headerName": "Criado em", "flex": 1},
                        {
                            "field": "actions",
                            "headerName": "Ações",
                            "cellRenderer": "agGroupCellRenderer",
                            "width": 130,
                            "cellRendererParams": {},
                        },
                    ],
                    rowData=[],
                    defaultColDef={"resizable": True, "sortable": True, "filter": True},
                    dashGridOptions={"pagination": True, "paginationPageSize": 20},
                    style={"height": "500px"},
                    className="ag-theme-alpine-dark",
                )
            )
        ),
        dcc.Interval(id="clients-interval", interval=30_000, n_intervals=0),
    ],
    fluid=True,
)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("clients-grid", "rowData"),
    Input("clients-interval", "n_intervals"),
)
def load_clients(_n):
    from app.database import get_session, Client

    with get_session() as session:
        clients = session.query(Client).order_by(Client.id.desc()).all()
        rows = [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email or "",
                "phone": c.phone or "",
                "status": c.status,
                "created_at": c.created_at.strftime("%d/%m/%Y") if c.created_at else "",
            }
            for c in clients
        ]
    return rows


@callback(
    Output("clients-delete-modal", "is_open"),
    Output("clients-delete-id-store", "data"),
    Input("clients-grid", "cellRendererData"),
    Input("clients-cancel-delete", "n_clicks"),
    Input("clients-confirm-delete", "n_clicks"),
    State("clients-delete-id-store", "data"),
    State("clients-delete-modal", "is_open"),
    prevent_initial_call=True,
)
def handle_delete_flow(cell_data, _cancel, _confirm, stored_id, is_open):
    from dash import ctx
    from app.database import get_session, Client

    trigger = ctx.triggered_id

    if trigger == "clients-grid" and cell_data:
        value = cell_data.get("value")
        if value == "delete":
            row_id = cell_data.get("rowId")
            return True, row_id

    if trigger == "clients-cancel-delete":
        return False, no_update

    if trigger == "clients-confirm-delete" and stored_id is not None:
        with get_session() as session:
            client = session.get(Client, int(stored_id))
            if client:
                session.delete(client)
        return False, None

    return is_open, no_update
