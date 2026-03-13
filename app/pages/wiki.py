"""Wiki / knowledge base page."""

import dash
from dash import html, dcc, callback, Output, Input, State, no_update
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/wiki", name="Wiki")

layout = dbc.Container(
    [
        dcc.Store(id="wiki-refresh-store", data=0),
        dbc.Row(
            dbc.Col(html.H2("Wiki / Base de Conhecimento"), className="mb-4 mt-2")
        ),

        # Add article form
        dbc.Card(
            [
                dbc.CardHeader("Nova Entrada"),
                dbc.CardBody(
                    [
                        dbc.Alert(id="wiki-alert", is_open=False, color="danger", dismissable=True),
                        dbc.Row(
                            dbc.Col(
                                [
                                    dbc.Label("Conteúdo (Markdown) *"),
                                    dbc.Textarea(
                                        id="wiki-content-input",
                                        placeholder="Escreva em Markdown...\n\n## Título\n\nConteúdo da nota...",
                                        rows=6,
                                        style={"fontFamily": "monospace"},
                                    ),
                                ],
                                className="mb-3",
                            )
                        ),
                        dbc.Button(
                            [html.I(className="bi bi-journal-plus me-2"), "Publicar"],
                            id="wiki-save-btn",
                            color="primary",
                        ),
                    ]
                ),
            ],
            className="mb-4",
        ),

        # Notes list rendered as Markdown
        html.Div(id="wiki-notes-list"),
    ],
    fluid=True,
)


@callback(
    Output("wiki-notes-list", "children"),
    Input("wiki-refresh-store", "data"),
)
def load_wiki_notes(_refresh):
    from app.database import get_session, Note

    with get_session() as session:
        # Show notes without a specific client association as wiki articles
        notes = (
            session.query(Note)
            .order_by(Note.created_at.desc())
            .limit(50)
            .all()
        )

        if not notes:
            return html.P("Nenhuma entrada na wiki ainda.", className="text-muted")

        cards = []
        for note in notes:
            cards.append(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dcc.Markdown(
                                note.content,
                                dangerously_allow_html=False,
                                className="mb-1",
                            ),
                            html.Hr(className="my-1"),
                            html.Small(
                                note.created_at.strftime("%d/%m/%Y %H:%M") if note.created_at else "",
                                className="text-muted",
                            ),
                        ]
                    ),
                    className="mb-3",
                )
            )
        return cards


@callback(
    Output("wiki-alert", "children"),
    Output("wiki-alert", "is_open"),
    Output("wiki-refresh-store", "data"),
    Output("wiki-content-input", "value"),
    Input("wiki-save-btn", "n_clicks"),
    State("wiki-content-input", "value"),
    State("wiki-refresh-store", "data"),
    prevent_initial_call=True,
)
def save_wiki_note(_n, content, refresh):
    if not content or not content.strip():
        return "Conteúdo é obrigatório.", True, no_update, no_update

    from datetime import datetime
    from app.database import get_session, Note

    try:
        with get_session() as session:
            note = Note(
                content=content.strip(),
                client_id=None,
                created_at=datetime.utcnow(),
            )
            session.add(note)
        return no_update, False, (refresh or 0) + 1, ""
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update
