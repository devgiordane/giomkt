"""Notes page."""

import dash
from dash import html, dcc, callback, Output, Input, State, no_update
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/notes", name="Notas")

layout = dbc.Container(
    [
        dcc.Store(id="notes-refresh-store", data=0),
        dbc.Row(
            [
                dbc.Col(html.H2("Notas"), md=8),
            ],
            className="mb-4 mt-2 align-items-center",
        ),

        # Add note form
        dbc.Card(
            [
                dbc.CardHeader("Nova Nota"),
                dbc.CardBody(
                    [
                        dbc.Alert(id="notes-alert", is_open=False, color="danger", dismissable=True),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Cliente (opcional)"),
                                        dcc.Dropdown(
                                            id="notes-client-select",
                                            placeholder="Selecione um cliente",
                                            clearable=True,
                                        ),
                                    ],
                                    md=4,
                                    className="mb-3",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label("Conteúdo *"),
                                        dbc.Textarea(
                                            id="notes-content-input",
                                            placeholder="Digite a nota aqui...",
                                            rows=3,
                                        ),
                                    ],
                                    md=8,
                                    className="mb-3",
                                ),
                            ]
                        ),
                        dbc.Button(
                            [html.I(className="bi bi-save me-2"), "Salvar Nota"],
                            id="notes-save-btn",
                            color="primary",
                        ),
                    ]
                ),
            ],
            className="mb-4",
        ),

        # Notes list
        html.Div(id="notes-list"),
    ],
    fluid=True,
)


@callback(
    Output("notes-client-select", "options"),
    Input("notes-refresh-store", "data"),
)
def load_clients(_refresh):
    from app.database import get_session, Client

    with get_session() as session:
        clients = session.query(Client).all()
        return [{"label": c.name, "value": c.id} for c in clients]


@callback(
    Output("notes-list", "children"),
    Input("notes-refresh-store", "data"),
)
def load_notes(_refresh):
    from app.database import get_session, Note, Client

    with get_session() as session:
        notes = session.query(Note).order_by(Note.created_at.desc()).limit(100).all()
        client_map = {c.id: c.name for c in session.query(Client).all()}

        if not notes:
            return html.P("Nenhuma nota encontrada.", className="text-muted")

        items = []
        for note in notes:
            client_label = client_map.get(note.client_id, "—") if note.client_id else "—"
            items.append(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Small(
                                                [
                                                    html.I(className="bi bi-person me-1"),
                                                    client_label,
                                                    " · ",
                                                    note.created_at.strftime("%d/%m/%Y %H:%M") if note.created_at else "",
                                                ],
                                                className="text-muted",
                                            ),
                                            html.P(note.content, className="mt-1 mb-0"),
                                        ],
                                        md=10,
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            html.I(className="bi bi-trash"),
                                            id={"type": "notes-delete-btn", "index": note.id},
                                            color="outline-danger",
                                            size="sm",
                                            className="float-end",
                                        ),
                                        md=2,
                                        className="d-flex justify-content-end align-items-center",
                                    ),
                                ]
                            )
                        ]
                    ),
                    className="mb-2",
                )
            )
        return items


@callback(
    Output("notes-alert", "children"),
    Output("notes-alert", "is_open"),
    Output("notes-refresh-store", "data"),
    Output("notes-content-input", "value"),
    Input("notes-save-btn", "n_clicks"),
    State("notes-content-input", "value"),
    State("notes-client-select", "value"),
    State("notes-refresh-store", "data"),
    prevent_initial_call=True,
)
def save_note(_n, content, client_id, refresh):
    if not content or not content.strip():
        return "Conteúdo é obrigatório.", True, no_update, no_update

    from datetime import datetime
    from app.database import get_session, Note

    try:
        with get_session() as session:
            note = Note(
                content=content.strip(),
                client_id=int(client_id) if client_id else None,
                created_at=datetime.utcnow(),
            )
            session.add(note)
        return no_update, False, (refresh or 0) + 1, ""
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update


@callback(
    Output("notes-refresh-store", "data", allow_duplicate=True),
    Input({"type": "notes-delete-btn", "index": dash.ALL}, "n_clicks"),
    State("notes-refresh-store", "data"),
    prevent_initial_call=True,
)
def delete_note(n_clicks_list, refresh):
    from dash import ctx
    from app.database import get_session, Note

    if not any(n for n in n_clicks_list if n):
        return no_update

    triggered = ctx.triggered_id
    if triggered and isinstance(triggered, dict):
        note_id = triggered.get("index")
        if note_id:
            with get_session() as session:
                note = session.get(Note, int(note_id))
                if note:
                    session.delete(note)
            return (refresh or 0) + 1

    return no_update
