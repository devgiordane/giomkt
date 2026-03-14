"""New client form page."""

import dash
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/clients/new", name="Novo Cliente")

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = dbc.Container(
    [
        dcc.Location(id="client-form-location", refresh=True),
        dbc.Row(
            dbc.Col(
                [
                    html.H2("Novo Cliente", className="mb-4 mt-2"),
                    dbc.Alert(id="client-form-alert", is_open=False, dismissable=True),
                    dbc.Form(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("Nome *"),
                                            dbc.Input(
                                                id="cf-name",
                                                type="text",
                                                placeholder="Nome do cliente",
                                            ),
                                        ],
                                        md=6,
                                        className="mb-3",
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Email"),
                                            dbc.Input(
                                                id="cf-email",
                                                type="email",
                                                placeholder="email@exemplo.com",
                                            ),
                                        ],
                                        md=6,
                                        className="mb-3",
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("Telefone"),
                                            dbc.Input(
                                                id="cf-phone",
                                                type="text",
                                                placeholder="+55 11 99999-9999",
                                            ),
                                        ],
                                        md=6,
                                        className="mb-3",
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Status"),
                                            dbc.Select(
                                                id="cf-status",
                                                options=[
                                                    {"label": "Ativo", "value": "active"},
                                                    {"label": "Inativo", "value": "inactive"},
                                                ],
                                                value="active",
                                            ),
                                        ],
                                        md=6,
                                        className="mb-3",
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("FB Ad Account ID"),
                                            dbc.Input(
                                                id="cf-fb-account",
                                                type="text",
                                                placeholder="act_XXXXXXXXXX",
                                            ),
                                        ],
                                        md=6,
                                        className="mb-3",
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("FB Access Token"),
                                            dbc.Input(
                                                id="cf-fb-token",
                                                type="password",
                                                placeholder="EAAxxxxx...",
                                            ),
                                        ],
                                        md=6,
                                        className="mb-3",
                                    ),
                                ]
                            ),
                            dbc.Row(
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            [html.I(className="bi bi-save me-2"), "Salvar"],
                                            id="cf-save-btn",
                                            color="primary",
                                            className="me-2",
                                        ),
                                        dbc.Button(
                                            "Cancelar",
                                            href="/clients",
                                            color="secondary",
                                            outline=True,
                                        ),
                                    ]
                                )
                            ),
                        ]
                    ),
                ],
                md=10,
                lg=8,
            ),
            justify="center",
        ),
    ],
    fluid=True,
)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("client-form-location", "href"),
    Output("client-form-alert", "children"),
    Output("client-form-alert", "color"),
    Output("client-form-alert", "is_open"),
    Input("cf-save-btn", "n_clicks"),
    State("cf-name", "value"),
    State("cf-email", "value"),
    State("cf-phone", "value"),
    State("cf-status", "value"),
    State("cf-fb-account", "value"),
    State("cf-fb-token", "value"),
    prevent_initial_call=True,
)
def save_client(_n, name, email, phone, status, fb_account, fb_token):
    if not name or not name.strip():
        return dash.no_update, "O campo Nome é obrigatório.", "danger", True

    from app.database import get_session, Client

    try:
        with get_session() as session:
            client = Client(
                name=name.strip(),
                email=email.strip() if email else None,
                phone=phone.strip() if phone else None,
                status=status or "active",
                fb_ad_account_id=fb_account.strip() if fb_account else None,
                fb_token=fb_token.strip() if fb_token else None,
            )
            session.add(client)
        return "/clients", dash.no_update, dash.no_update, False
    except Exception as exc:
        return dash.no_update, f"Erro ao salvar: {exc}", "danger", True
