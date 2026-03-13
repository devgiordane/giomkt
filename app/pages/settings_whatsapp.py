"""WhatsApp / EvolutionAPI settings page."""

import json
import os

import dash
from dash import html, dcc, callback, Output, Input, State, no_update
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/settings/whatsapp", name="WhatsApp")

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "whatsapp_settings.json")


def _load_settings() -> dict:
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    # Fallback to env vars
    from app.config import EVOLUTION_API_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE
    return {
        "base_url": EVOLUTION_API_URL,
        "api_key": EVOLUTION_API_KEY,
        "instance_name": EVOLUTION_INSTANCE,
    }


def _save_settings(settings: dict) -> None:
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(html.H2("Configurações – WhatsApp (EvolutionAPI)"), className="mb-4 mt-2")
        ),
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.Alert(id="wa-settings-alert", is_open=False, dismissable=True),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("Base URL"),
                                            dbc.Input(
                                                id="wa-base-url",
                                                type="text",
                                                placeholder="http://localhost:8080",
                                            ),
                                        ],
                                        md=6,
                                        className="mb-3",
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("API Key"),
                                            dbc.Input(
                                                id="wa-api-key",
                                                type="password",
                                                placeholder="your-api-key",
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
                                        dbc.Label("Instance Name"),
                                        dbc.Input(
                                            id="wa-instance-name",
                                            type="text",
                                            placeholder="default",
                                        ),
                                    ],
                                    md=6,
                                    className="mb-3",
                                )
                            ),
                            dbc.Row(
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            [html.I(className="bi bi-save me-2"), "Salvar"],
                                            id="wa-save-btn",
                                            color="primary",
                                            className="me-2",
                                        ),
                                        dbc.Button(
                                            [html.I(className="bi bi-wifi me-2"), "Testar Conexão"],
                                            id="wa-test-btn",
                                            color="outline-info",
                                        ),
                                    ]
                                )
                            ),
                        ]
                    )
                ),
                md=10,
                lg=8,
            ),
            justify="center",
        ),
        # Hidden store to pre-fill form on load
        dcc.Store(id="wa-settings-loaded", data=False),
    ],
    fluid=True,
)


@callback(
    Output("wa-base-url", "value"),
    Output("wa-api-key", "value"),
    Output("wa-instance-name", "value"),
    Output("wa-settings-loaded", "data"),
    Input("wa-settings-loaded", "data"),
)
def prefill_settings(loaded):
    if loaded:
        return no_update, no_update, no_update, no_update
    settings = _load_settings()
    return settings.get("base_url", ""), settings.get("api_key", ""), settings.get("instance_name", ""), True


@callback(
    Output("wa-settings-alert", "children"),
    Output("wa-settings-alert", "color"),
    Output("wa-settings-alert", "is_open"),
    Input("wa-save-btn", "n_clicks"),
    Input("wa-test-btn", "n_clicks"),
    State("wa-base-url", "value"),
    State("wa-api-key", "value"),
    State("wa-instance-name", "value"),
    prevent_initial_call=True,
)
def handle_buttons(_save, _test, base_url, api_key, instance_name):
    from dash import ctx
    import requests as req

    trigger = ctx.triggered_id

    if trigger == "wa-save-btn":
        if not base_url or not instance_name:
            return "Base URL e Instance Name são obrigatórios.", "danger", True
        try:
            _save_settings(
                {"base_url": base_url.strip(), "api_key": api_key or "", "instance_name": instance_name.strip()}
            )
            return "Configurações salvas com sucesso.", "success", True
        except Exception as exc:
            return f"Erro ao salvar: {exc}", "danger", True

    if trigger == "wa-test-btn":
        url = f"{(base_url or '').rstrip('/')}/instance/fetchInstances"
        headers = {"apikey": api_key or ""}
        try:
            response = req.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return f"Conexão OK! Status {response.status_code}.", "success", True
            else:
                return f"Resposta inesperada: HTTP {response.status_code}.", "warning", True
        except Exception as exc:
            return f"Falha na conexão: {exc}", "danger", True

    return no_update, no_update, False
