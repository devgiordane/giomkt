"""Label management page."""

import dash
from dash import html, dcc, callback, Output, Input, State, no_update, ctx, ALL
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/labels", name="Etiquetas")

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = dbc.Container(
    [
        dcc.Store(id="labels-refresh-store", data=0),
        dcc.Store(id="labels-edit-id-store"),
        dcc.Store(id="labels-del-id-store"),

        # Add modal
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Nova Etiqueta")),
                dbc.ModalBody([
                    dbc.Alert(id="labels-add-alert", is_open=False, color="danger"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Nome *"),
                            dbc.Input(id="labels-add-name", placeholder="Nome da etiqueta"),
                        ], className="mb-3"),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Cor"),
                            dbc.Input(id="labels-add-color", type="color", value="#6c757d"),
                        ], className="mb-3"),
                    ]),
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancelar", id="labels-add-cancel", color="secondary", className="me-2"),
                    dbc.Button("Salvar", id="labels-add-save", color="primary"),
                ]),
            ],
            id="labels-add-modal",
            is_open=False,
        ),

        # Edit modal
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Editar Etiqueta")),
                dbc.ModalBody([
                    dbc.Alert(id="labels-edit-alert", is_open=False, color="danger"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Nome *"),
                            dbc.Input(id="labels-edit-name", placeholder="Nome da etiqueta"),
                        ], className="mb-3"),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Cor"),
                            dbc.Input(id="labels-edit-color", type="color", value="#6c757d"),
                        ], className="mb-3"),
                    ]),
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancelar", id="labels-edit-cancel", color="secondary", className="me-2"),
                    dbc.Button("Salvar", id="labels-edit-save", color="primary"),
                ]),
            ],
            id="labels-edit-modal",
            is_open=False,
        ),

        # Delete confirm modal
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Confirmar exclusão")),
                dbc.ModalBody("Tem certeza que deseja excluir esta etiqueta?"),
                dbc.ModalFooter([
                    dbc.Button("Cancelar", id="labels-del-cancel", color="secondary", className="me-2"),
                    dbc.Button("Excluir", id="labels-del-confirm", color="danger"),
                ]),
            ],
            id="labels-del-modal",
            is_open=False,
        ),

        # Header
        dbc.Row([
            dbc.Col(html.H2("Etiquetas"), md=8),
            dbc.Col(
                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-2"), "Nova Etiqueta"],
                    id="labels-open-add-btn",
                    color="primary",
                ),
                md=4,
                className="text-end",
            ),
        ], className="mb-4 mt-2 align-items-center"),

        # Labels list
        html.Div(id="labels-list"),

        # Toast
        dbc.Toast(
            id="labels-toast",
            header="",
            is_open=False,
            dismissable=True,
            duration=3000,
            style={"position": "fixed", "bottom": "1rem", "right": "1rem", "zIndex": 9999},
        ),
    ],
    fluid=True,
)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("labels-list", "children"),
    Input("labels-refresh-store", "data"),
)
def render_labels(_refresh):
    from app.database import get_session, TaskLabel

    with get_session() as session:
        labels = session.query(TaskLabel).order_by(TaskLabel.name).all()
        label_data = [{"id": lb.id, "name": lb.name, "color": lb.color} for lb in labels]

    if not label_data:
        return dbc.Alert("Nenhuma etiqueta cadastrada. Clique em 'Nova Etiqueta' para criar.", color="info")

    items = []
    for lb in label_data:
        items.append(
            dbc.ListGroupItem(
                dbc.Row([
                    dbc.Col(
                        dbc.Badge(
                            lb["name"],
                            style={
                                "backgroundColor": lb["color"],
                                "color": "#fff",
                                "fontSize": "0.9rem",
                                "padding": "6px 12px",
                            },
                        ),
                        className="d-flex align-items-center",
                    ),
                    dbc.Col(
                        html.Div([
                            html.Span(
                                lb["color"],
                                className="text-muted me-3",
                                style={"fontFamily": "monospace"},
                            ),
                            html.Span(
                                style={
                                    "display": "inline-block",
                                    "width": "20px",
                                    "height": "20px",
                                    "backgroundColor": lb["color"],
                                    "borderRadius": "4px",
                                    "border": "1px solid #ccc",
                                    "verticalAlign": "middle",
                                    "marginRight": "12px",
                                }
                            ),
                        ], className="d-inline-flex align-items-center"),
                    ),
                    dbc.Col(
                        html.Div([
                            dbc.Button(
                                html.I(className="bi bi-pencil"),
                                id={"type": "label-edit-btn", "index": lb["id"]},
                                size="sm", color="link", className="p-0 me-2 text-secondary",
                            ),
                            dbc.Button(
                                html.I(className="bi bi-trash"),
                                id={"type": "label-del-btn", "index": lb["id"]},
                                size="sm", color="link", className="p-0 text-danger",
                            ),
                        ], className="d-flex justify-content-end"),
                        width="auto",
                    ),
                ], align="center", className="g-2"),
                className="py-2",
            )
        )

    return dbc.ListGroup(items, flush=True)


# Toggle add modal
@callback(
    Output("labels-add-modal", "is_open"),
    Output("labels-add-name", "value"),
    Output("labels-add-color", "value"),
    Input("labels-open-add-btn", "n_clicks"),
    Input("labels-add-cancel", "n_clicks"),
    State("labels-add-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_add_modal(_open, _cancel, is_open):
    triggered = ctx.triggered_id
    if triggered == "labels-open-add-btn":
        return True, "", "#6c757d"
    return False, no_update, no_update


# Save new label
@callback(
    Output("labels-add-alert", "children"),
    Output("labels-add-alert", "is_open"),
    Output("labels-add-modal", "is_open", allow_duplicate=True),
    Output("labels-refresh-store", "data", allow_duplicate=True),
    Output("labels-toast", "children", allow_duplicate=True),
    Output("labels-toast", "header", allow_duplicate=True),
    Output("labels-toast", "is_open", allow_duplicate=True),
    Input("labels-add-save", "n_clicks"),
    State("labels-add-name", "value"),
    State("labels-add-color", "value"),
    State("labels-refresh-store", "data"),
    prevent_initial_call=True,
)
def save_new_label(_n, name, color, refresh):
    if not name or not name.strip():
        return "Nome é obrigatório.", True, no_update, no_update, no_update, no_update, no_update

    from app.database import get_session, TaskLabel

    try:
        with get_session() as session:
            lb = TaskLabel(name=name.strip(), color=color or "#6c757d")
            session.add(lb)
        return no_update, False, False, (refresh or 0) + 1, "Etiqueta criada!", "Etiquetas", True
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update, no_update, no_update, no_update


# Open edit modal
@callback(
    Output("labels-edit-modal", "is_open"),
    Output("labels-edit-id-store", "data"),
    Output("labels-edit-name", "value"),
    Output("labels-edit-color", "value"),
    Input({"type": "label-edit-btn", "index": ALL}, "n_clicks"),
    Input("labels-edit-cancel", "n_clicks"),
    State("labels-edit-modal", "is_open"),
    prevent_initial_call=True,
)
def open_edit_modal(edit_clicks, _cancel, is_open):
    triggered = ctx.triggered_id
    if triggered == "labels-edit-cancel" or not any(c for c in edit_clicks if c):
        return False, no_update, no_update, no_update

    label_id = triggered["index"]

    from app.database import get_session, TaskLabel

    with get_session() as session:
        lb = session.get(TaskLabel, label_id)
        if not lb:
            return False, no_update, no_update, no_update
        return True, label_id, lb.name, lb.color


# Save edited label
@callback(
    Output("labels-edit-alert", "children"),
    Output("labels-edit-alert", "is_open"),
    Output("labels-edit-modal", "is_open", allow_duplicate=True),
    Output("labels-refresh-store", "data", allow_duplicate=True),
    Output("labels-toast", "children", allow_duplicate=True),
    Output("labels-toast", "header", allow_duplicate=True),
    Output("labels-toast", "is_open", allow_duplicate=True),
    Input("labels-edit-save", "n_clicks"),
    State("labels-edit-id-store", "data"),
    State("labels-edit-name", "value"),
    State("labels-edit-color", "value"),
    State("labels-refresh-store", "data"),
    prevent_initial_call=True,
)
def save_edited_label(_n, label_id, name, color, refresh):
    if not name or not name.strip():
        return "Nome é obrigatório.", True, no_update, no_update, no_update, no_update, no_update

    from app.database import get_session, TaskLabel

    try:
        with get_session() as session:
            lb = session.get(TaskLabel, label_id)
            if not lb:
                return "Etiqueta não encontrada.", True, no_update, no_update, no_update, no_update, no_update
            lb.name = name.strip()
            lb.color = color or "#6c757d"
        return no_update, False, False, (refresh or 0) + 1, "Etiqueta atualizada!", "Etiquetas", True
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update, no_update, no_update, no_update


# Open delete modal
@callback(
    Output("labels-del-modal", "is_open"),
    Output("labels-del-id-store", "data"),
    Input({"type": "label-del-btn", "index": ALL}, "n_clicks"),
    Input("labels-del-cancel", "n_clicks"),
    State("labels-del-modal", "is_open"),
    prevent_initial_call=True,
)
def open_delete_modal(del_clicks, _cancel, is_open):
    triggered = ctx.triggered_id
    if triggered == "labels-del-cancel" or not any(c for c in del_clicks if c):
        return False, no_update
    return True, triggered["index"]


# Confirm delete
@callback(
    Output("labels-del-modal", "is_open", allow_duplicate=True),
    Output("labels-refresh-store", "data", allow_duplicate=True),
    Output("labels-toast", "children", allow_duplicate=True),
    Output("labels-toast", "header", allow_duplicate=True),
    Output("labels-toast", "is_open", allow_duplicate=True),
    Input("labels-del-confirm", "n_clicks"),
    State("labels-del-id-store", "data"),
    State("labels-refresh-store", "data"),
    prevent_initial_call=True,
)
def confirm_delete(_n, label_id, refresh):
    if not label_id:
        return False, no_update, no_update, no_update, no_update

    from app.database import get_session, TaskLabel

    with get_session() as session:
        lb = session.get(TaskLabel, label_id)
        if lb:
            session.delete(lb)
    return False, (refresh or 0) + 1, "Etiqueta excluída.", "Etiquetas", True
