"""AI Assistant — universal content processing page."""

import json
from datetime import datetime

import dash
from dash import html, dcc, callback, Output, Input, State, no_update, ctx
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/ai-assistant", name="Assistente IA")

ACTION_OPTIONS = [
    {"label": "Criar tarefas", "value": "create_tasks"},
    {"label": "Gerar mensagem para cliente", "value": "generate_message"},
    {"label": "Resumir", "value": "summarize"},
    {"label": "Extrair dados", "value": "extract_data"},
    {"label": "Analisar campanha", "value": "analyze_campaign"},
]

layout = dbc.Container([
    dcc.Store(id="ai-result-store"),

    # Header
    dbc.Row([
        dbc.Col(html.H2([html.I(className="bi bi-robot me-2"), "Assistente IA"]), md=8),
    ], className="mb-4 mt-2"),

    # Input area
    dbc.Row([
        dbc.Col([
            dbc.Textarea(
                id="ai-content-input",
                placeholder="Cole aqui qualquer conteúdo: campanha, conversa com cliente, briefing, relatório, ideias, copy, tabela...",
                rows=10,
                className="ai-textarea mb-3",
            ),

            dbc.Label("Selecionar ação:", className="fw-bold mb-2"),
            dbc.RadioItems(
                id="ai-action-select",
                options=ACTION_OPTIONS,
                value="create_tasks",
                inline=True,
                className="mb-3",
            ),

            dbc.Button(
                [html.I(className="bi bi-lightning-charge me-2"), "Processar"],
                id="ai-process-btn",
                color="primary",
                size="lg",
                className="mb-4",
            ),
        ]),
    ]),

    # Output area
    dcc.Loading(
        html.Div(id="ai-output-area"),
        type="circle",
        color="#0d6efd",
    ),

    dbc.Toast(id="ai-toast", header="Assistente IA", is_open=False, dismissable=True, duration=3000,
              style={"position": "fixed", "bottom": "1rem", "right": "1rem", "zIndex": 9999}),
], fluid=True)


# ---------------------------------------------------------------------------
# Process content
# ---------------------------------------------------------------------------

@callback(
    Output("ai-result-store", "data"),
    Output("ai-output-area", "children"),
    Input("ai-process-btn", "n_clicks"),
    State("ai-content-input", "value"),
    State("ai-action-select", "value"),
    prevent_initial_call=True,
)
def process_content(_n, content, action):
    if not content or not content.strip():
        return no_update, dbc.Alert("Cole algum conteúdo antes de processar.", color="warning")

    from app.services.ai_assistant import process_content as ai_process

    result = ai_process(action, content.strip())

    if "error" in result:
        return result, dbc.Alert(result["error"], color="danger")

    return result, _render_result(action, result)


def _render_result(action, result):
    """Render the AI result based on action type."""
    if action == "create_tasks":
        return _render_tasks(result)
    elif action == "generate_message":
        return _render_message(result)
    elif action == "summarize":
        return _render_summary(result)
    elif action == "extract_data":
        return _render_data(result)
    elif action == "analyze_campaign":
        return _render_campaign(result)
    return html.Pre(json.dumps(result, indent=2, ensure_ascii=False))


def _render_tasks(result):
    tasks = result.get("tasks", [])
    if not tasks:
        return dbc.Alert("Nenhuma tarefa identificada.", color="info")

    priority_map = {1: "danger", 2: "warning", 3: "primary", 4: "secondary"}
    priority_labels = {1: "P1", 2: "P2", 3: "P3", 4: "P4"}

    rows = []
    for i, t in enumerate(tasks):
        p = t.get("priority", 4)
        rows.append(html.Tr([
            html.Td(str(i + 1)),
            html.Td(t.get("title", "")),
            html.Td(dbc.Badge(priority_labels.get(p, "P4"), color=priority_map.get(p, "secondary"))),
            html.Td(t.get("due_date") or "—"),
        ]))

    table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("#"), html.Th("Tarefa"), html.Th("Prioridade"), html.Th("Data"),
        ])),
        html.Tbody(rows),
    ], bordered=True, hover=True, responsive=True, className="mt-3")

    return html.Div([
        html.H5(f"{len(tasks)} tarefas identificadas"),
        table,
        dbc.Button(
            [html.I(className="bi bi-check2-square me-2"), "Salvar no sistema"],
            id="ai-save-tasks-btn",
            color="success",
            className="mt-2",
        ),
    ])


def _render_message(result):
    msg = result.get("message", "")
    subject = result.get("subject", "")
    return dbc.Card([
        dbc.CardHeader("Mensagem gerada"),
        dbc.CardBody([
            html.P([html.Strong("Assunto: "), subject]) if subject else None,
            html.Hr() if subject else None,
            html.P(msg, style={"whiteSpace": "pre-wrap"}),
            dcc.Clipboard(target_id="ai-msg-text", className="mt-2"),
            html.Div(msg, id="ai-msg-text", style={"display": "none"}),
        ]),
    ], className="mt-3")


def _render_summary(result):
    summary = result.get("summary", "")
    points = result.get("key_points", [])
    return dbc.Card([
        dbc.CardHeader("Resumo"),
        dbc.CardBody([
            html.P(summary, style={"whiteSpace": "pre-wrap"}),
            html.Hr() if points else None,
            html.H6("Pontos-chave:") if points else None,
            dbc.ListGroup([
                dbc.ListGroupItem([html.I(className="bi bi-check-circle me-2"), p])
                for p in points
            ], flush=True) if points else None,
        ]),
    ], className="mt-3")


def _render_data(result):
    data = result.get("data", [])
    if not data:
        return dbc.Alert("Nenhum dado extraído.", color="info")

    rows = [html.Tr([html.Td(d.get("field", "")), html.Td(str(d.get("value", "")))]) for d in data]
    return dbc.Table([
        html.Thead(html.Tr([html.Th("Campo"), html.Th("Valor")])),
        html.Tbody(rows),
    ], bordered=True, hover=True, responsive=True, className="mt-3")


def _render_campaign(result):
    analysis = result.get("analysis", "")
    recs = result.get("recommendations", [])
    metrics = result.get("metrics", {})

    metric_cards = []
    metric_labels = {"cpa": "CPA", "ctr": "CTR", "roas": "ROAS"}
    for key, label in metric_labels.items():
        val = metrics.get(key)
        if val is not None:
            metric_cards.append(
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.P(label, className="kpi-label"),
                    html.H4(str(val), className="kpi-value"),
                ]), className="kpi-card"), md=4)
            )

    return html.Div([
        dbc.Row(metric_cards, className="mb-3") if metric_cards else None,
        dbc.Card([
            dbc.CardHeader("Análise"),
            dbc.CardBody(html.P(analysis, style={"whiteSpace": "pre-wrap"})),
        ], className="mt-3"),
        html.H6("Recomendações:", className="mt-3") if recs else None,
        dbc.ListGroup([
            dbc.ListGroupItem([html.I(className="bi bi-lightbulb me-2"), r])
            for r in recs
        ], flush=True, className="mb-3") if recs else None,
    ])


# ---------------------------------------------------------------------------
# Save tasks to DB
# ---------------------------------------------------------------------------

@callback(
    Output("ai-toast", "children"),
    Output("ai-toast", "is_open"),
    Output("ai-output-area", "children", allow_duplicate=True),
    Input("ai-save-tasks-btn", "n_clicks"),
    State("ai-result-store", "data"),
    prevent_initial_call=True,
)
def save_tasks(_n, result):
    if not result or "tasks" not in result:
        return "Nenhuma tarefa para salvar.", True, no_update

    from app.database import get_session, Task

    tasks = result["tasks"]
    try:
        with get_session() as session:
            for t in tasks:
                due = None
                if t.get("due_date"):
                    try:
                        from datetime import date
                        due = date.fromisoformat(t["due_date"])
                    except (ValueError, TypeError):
                        pass

                session.add(Task(
                    title=t.get("title", "Sem título"),
                    priority=t.get("priority", 4),
                    due_date=due,
                    section="Para fazer",
                    status="pending",
                    source="manual",
                    created_at=datetime.utcnow(),
                ))

        return f"{len(tasks)} tarefas salvas!", True, dbc.Alert(
            f"{len(tasks)} tarefas salvas com sucesso no sistema!",
            color="success",
            className="mt-3",
        )
    except Exception as exc:
        return f"Erro: {exc}", True, no_update
