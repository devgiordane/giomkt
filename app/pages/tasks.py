"""Tasks page – Todoist-inspired task management."""

from datetime import date, datetime

import dash
from dash import html, dcc, callback, Output, Input, State, no_update, ctx, ALL, MATCH
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/tasks", name="Tarefas")

# ---------------------------------------------------------------------------
# Priority config
# ---------------------------------------------------------------------------

PRIORITY_OPTIONS = [
    {"label": "🚩 Prioridade 1 (Alta)", "value": 1},
    {"label": "🔶 Prioridade 2", "value": 2},
    {"label": "🔷 Prioridade 3", "value": 3},
    {"label": "⬜ Prioridade 4 (Nenhuma)", "value": 4},
]

PRIORITY_COLORS = {1: "danger", 2: "warning", 3: "primary", 4: "secondary"}
PRIORITY_ICONS = {1: "bi bi-flag-fill text-danger", 2: "bi bi-flag-fill text-warning", 3: "bi bi-flag-fill text-primary", 4: "bi bi-flag text-secondary"}

DEFAULT_SECTIONS = ["Para fazer", "Fazendo", "Feito"]

RECURRENCE_LABELS = {
    "": "Sem recorrência",
    "daily": "Diariamente",
    "weekdays": "Dias úteis (Seg-Sex)",
    "weekly": "Semanalmente",
    "weekly:0": "Toda Segunda",
    "weekly:1": "Toda Terça",
    "weekly:2": "Toda Quarta",
    "weekly:3": "Toda Quinta",
    "weekly:4": "Toda Sexta",
    "weekly:5": "Todo Sábado",
    "weekly:6": "Todo Domingo",
    "monthly": "Mensalmente",
}

RECURRENCE_OPTIONS = [
    {"label": "Sem recorrência", "value": ""},
    {"label": "Diariamente", "value": "daily"},
    {"label": "Dias úteis (Seg-Sex)", "value": "weekdays"},
    {"label": "Semanalmente", "value": "weekly"},
    {"label": "Toda Segunda", "value": "weekly:0"},
    {"label": "Toda Terça", "value": "weekly:1"},
    {"label": "Toda Quarta", "value": "weekly:2"},
    {"label": "Toda Quinta", "value": "weekly:3"},
    {"label": "Toda Sexta", "value": "weekly:4"},
    {"label": "Todo Sábado", "value": "weekly:5"},
    {"label": "Todo Domingo", "value": "weekly:6"},
    {"label": "Mensalmente", "value": "monthly"},
]

# ---------------------------------------------------------------------------
# Modals
# ---------------------------------------------------------------------------

add_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Nova Tarefa")),
        dbc.ModalBody(
            [
                dbc.Alert(id="tasks-add-alert", is_open=False, color="danger"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Título *"),
                        dbc.Input(
                            id="tasks-add-title",
                            placeholder="O que precisa ser feito? (ex: Reunião 10h por 1h amanhã p1)",
                            debounce=True,
                        ),
                        html.Div(id="tasks-add-nlp-preview", className="quick-add-preview mt-1"),
                    ], className="mb-3"),
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Descrição"),
                        dbc.Textarea(id="tasks-add-desc", placeholder="Detalhes opcionais", rows=2),
                    ], className="mb-3"),
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Seção"),
                        dbc.Select(
                            id="tasks-add-section",
                            options=[{"label": s, "value": s} for s in DEFAULT_SECTIONS],
                            value="Para fazer",
                        ),
                    ], md=6, className="mb-3"),
                    dbc.Col([
                        dbc.Label("Prioridade"),
                        dbc.Select(
                            id="tasks-add-priority",
                            options=PRIORITY_OPTIONS,
                            value=4,
                        ),
                    ], md=6, className="mb-3"),
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Data de Vencimento"),
                        dbc.Input(id="tasks-add-due", type="date"),
                    ], md=6, className="mb-3"),
                    dbc.Col([
                        dbc.Label("Prazo Final (Deadline)"),
                        dbc.Input(id="tasks-add-deadline", type="date"),
                    ], md=6, className="mb-3"),
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Hora de início"),
                        dbc.Input(id="tasks-add-start-time", type="time", step=900),
                    ], md=6, className="mb-3"),
                    dbc.Col([
                        dbc.Label("Duração"),
                        dbc.Select(
                            id="tasks-add-duration",
                            options=[
                                {"label": "—", "value": ""},
                                {"label": "15 min", "value": "15"},
                                {"label": "30 min", "value": "30"},
                                {"label": "45 min", "value": "45"},
                                {"label": "1h", "value": "60"},
                                {"label": "1h30", "value": "90"},
                                {"label": "2h", "value": "120"},
                                {"label": "3h", "value": "180"},
                                {"label": "4h", "value": "240"},
                            ],
                            value="",
                        ),
                    ], md=6, className="mb-3"),
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Cliente (opcional)"),
                        dcc.Dropdown(id="tasks-add-client", placeholder="Selecione um cliente", clearable=True),
                    ], className="mb-3"),
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Subtarefa de (opcional)"),
                        dcc.Dropdown(id="tasks-add-parent", placeholder="Tarefa pai", clearable=True),
                    ], className="mb-3"),
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Recorrência"),
                        dbc.Select(
                            id="tasks-add-recurrence",
                            options=RECURRENCE_OPTIONS,
                            value="",
                        ),
                    ], md=6, className="mb-3"),
                    dbc.Col([
                        dbc.Label("Fim da recorrência"),
                        dbc.Input(id="tasks-add-recurrence-end", type="date"),
                    ], md=6, className="mb-3"),
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Etiquetas"),
                        dcc.Dropdown(
                            id="tasks-add-labels",
                            multi=True,
                            placeholder="Selecione etiquetas...",
                        ),
                    ], className="mb-3"),
                ]),
            ]
        ),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="tasks-add-cancel", color="secondary", className="me-2"),
            dbc.Button("Salvar", id="tasks-add-save", color="primary"),
        ]),
    ],
    id="tasks-add-modal",
    is_open=False,
    size="lg",
)

# Edit modal
edit_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Editar Tarefa")),
        dbc.ModalBody(
            [
                dcc.Store(id="tasks-edit-id-store"),
                dbc.Alert(id="tasks-edit-alert", is_open=False, color="danger"),
                dbc.Row([dbc.Col([
                    dbc.Label("Título *"),
                    dbc.Input(
                        id="tasks-edit-title",
                        placeholder="ex: Reunião 10h por 1h amanhã p1",
                        debounce=True,
                    ),
                    html.Div(id="tasks-edit-nlp-preview", className="quick-add-preview mt-1"),
                ], className="mb-3")]),
                dbc.Row([dbc.Col([dbc.Label("Descrição"), dbc.Textarea(id="tasks-edit-desc", rows=2)], className="mb-3")]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Seção"),
                        dbc.Select(id="tasks-edit-section", options=[{"label": s, "value": s} for s in DEFAULT_SECTIONS]),
                    ], md=6, className="mb-3"),
                    dbc.Col([
                        dbc.Label("Prioridade"),
                        dbc.Select(id="tasks-edit-priority", options=PRIORITY_OPTIONS),
                    ], md=6, className="mb-3"),
                ]),
                dbc.Row([
                    dbc.Col([dbc.Label("Data de Vencimento"), dbc.Input(id="tasks-edit-due", type="date")], md=6, className="mb-3"),
                    dbc.Col([dbc.Label("Prazo Final"), dbc.Input(id="tasks-edit-deadline", type="date")], md=6, className="mb-3"),
                ]),
                dbc.Row([
                    dbc.Col([dbc.Label("Hora de início"), dbc.Input(id="tasks-edit-start-time", type="time", step=900)], md=6, className="mb-3"),
                    dbc.Col([
                        dbc.Label("Duração"),
                        dbc.Select(
                            id="tasks-edit-duration",
                            options=[
                                {"label": "—", "value": ""},
                                {"label": "15 min", "value": "15"},
                                {"label": "30 min", "value": "30"},
                                {"label": "45 min", "value": "45"},
                                {"label": "1h", "value": "60"},
                                {"label": "1h30", "value": "90"},
                                {"label": "2h", "value": "120"},
                                {"label": "3h", "value": "180"},
                                {"label": "4h", "value": "240"},
                            ],
                            value="",
                        ),
                    ], md=6, className="mb-3"),
                ]),
                dbc.Row([dbc.Col([dbc.Label("Cliente"), dcc.Dropdown(id="tasks-edit-client", clearable=True)], className="mb-3")]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Recorrência"),
                        dbc.Select(id="tasks-edit-recurrence", options=RECURRENCE_OPTIONS, value=""),
                    ], md=6, className="mb-3"),
                    dbc.Col([
                        dbc.Label("Fim da recorrência"),
                        dbc.Input(id="tasks-edit-recurrence-end", type="date"),
                    ], md=6, className="mb-3"),
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Etiquetas"),
                        dcc.Dropdown(id="tasks-edit-labels", multi=True, placeholder="Selecione etiquetas..."),
                    ], className="mb-3"),
                ]),
            ]
        ),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="tasks-edit-cancel", color="secondary", className="me-2"),
            dbc.Button("Salvar", id="tasks-edit-save", color="primary"),
        ]),
    ],
    id="tasks-edit-modal",
    is_open=False,
    size="lg",
)

# Delete confirm modal
delete_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Confirmar exclusão")),
        dbc.ModalBody("Tem certeza que deseja excluir esta tarefa e todas as subtarefas?"),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="tasks-del-cancel", color="secondary", className="me-2"),
            dbc.Button("Excluir", id="tasks-del-confirm", color="danger"),
        ]),
    ],
    id="tasks-del-modal",
    is_open=False,
)

# Task detail offcanvas
detail_offcanvas = dbc.Offcanvas(
    [
        dcc.Store(id="tasks-detail-task-id"),
        html.Div(id="tasks-detail-content"),
        html.Hr(),
        html.H6("Comentários"),
        html.Div(id="tasks-comments-list"),
        dbc.Textarea(
            id="tasks-comment-input",
            placeholder="Adicionar comentário...",
            rows=2,
            className="mt-2",
        ),
        dbc.Button(
            "Enviar",
            id="tasks-comment-submit",
            color="primary",
            size="sm",
            className="mt-2",
        ),
    ],
    id="tasks-detail-offcanvas",
    title="Detalhes da Tarefa",
    placement="end",
    is_open=False,
    style={"width": "420px"},
)

# ---------------------------------------------------------------------------
# Helper to render task list
# ---------------------------------------------------------------------------

def render_task_item(task, client_map, indent=0, show_done=True):
    """Render a single task row with subtasks."""
    if task["status"] == "done" and not show_done:
        return None

    priority = task.get("priority", 4)
    flag_class = PRIORITY_ICONS.get(priority, PRIORITY_ICONS[4])
    is_done = task["status"] == "done"

    due = task.get("due_date")
    deadline = task.get("deadline")
    today_str = date.today().isoformat()
    due_color = "text-danger" if due and due < today_str and not is_done else "text-muted"

    badges = []
    if task.get("client"):
        badges.append(dbc.Badge(task["client"], color="info", className="me-1"))
    if task.get("source") == "whatsapp":
        badges.append(dbc.Badge("WhatsApp", color="success", className="me-1"))
    if due:
        badges.append(dbc.Badge(f"Vence {due}", color="light", text_color="dark", className=f"me-1 {due_color}"))
    if deadline:
        badges.append(dbc.Badge(f"Prazo {deadline}", color="danger", className="me-1"))
    if task.get("subtask_count", 0) > 0:
        badges.append(dbc.Badge(f"{task['subtask_count']} subtarefa(s)", color="secondary", className="me-1"))
    if task.get("recurrence"):
        badges.append(dbc.Badge(
            [html.Span("🔁 "), RECURRENCE_LABELS.get(task["recurrence"], task["recurrence"])],
            color="light",
            text_color="dark",
            className="me-1",
        ))
    # Label badges
    for lb in task.get("labels", []):
        badges.append(dbc.Badge(
            lb["name"],
            style={"backgroundColor": lb["color"], "color": "#fff"},
            className="me-1",
        ))

    row = dbc.ListGroupItem(
        dbc.Row([
            # Checkbox
            dbc.Col(
                dbc.Checklist(
                    options=[{"label": "", "value": task["id"]}],
                    value=[task["id"]] if is_done else [],
                    id={"type": "task-check", "index": task["id"]},
                    inline=True,
                    style={"marginTop": "2px"},
                ),
                width="auto",
            ),
            # Flag
            dbc.Col(
                html.I(className=flag_class, style={"fontSize": "0.9rem"}),
                width="auto",
            ),
            # Title + badges
            dbc.Col([
                dbc.Button(
                    task["title"],
                    id={"type": "task-title-btn", "index": task["id"]},
                    color="link",
                    className="p-0 text-start",
                    style={
                        "textDecoration": "line-through" if is_done else "none",
                        "color": "#888" if is_done else "inherit",
                        "fontWeight": "500",
                        "fontSize": "inherit",
                    },
                ),
                html.Div(badges, className="mt-1") if badges else None,
            ]),
            # Actions
            dbc.Col(
                html.Div([
                    dbc.Button(
                        html.I(className="bi bi-pencil"),
                        id={"type": "task-edit-btn", "index": task["id"]},
                        size="sm", color="link", className="p-0 me-2 text-secondary",
                    ),
                    dbc.Button(
                        html.I(className="bi bi-trash"),
                        id={"type": "task-del-btn", "index": task["id"]},
                        size="sm", color="link", className="p-0 text-danger",
                    ),
                ], className="d-flex justify-content-end"),
                width="auto",
            ),
        ], align="center", className="g-2"),
        style={"paddingLeft": f"{20 + indent * 24}px", "borderLeft": "none"},
        className="border-bottom py-2",
    )

    children = [row]
    for sub in task.get("subtasks", []):
        item = render_task_item(sub, client_map, indent=indent + 1, show_done=show_done)
        if item:
            children.append(item)

    return html.Div(children)


def render_section(section_name, tasks, client_map, show_done):
    items = []
    for t in tasks:
        item = render_task_item(t, client_map, show_done=show_done)
        if item:
            items.append(item)

    count = len([t for t in tasks if t["status"] != "done" or show_done])

    return dbc.Card([
        dbc.CardHeader(
            dbc.Row([
                dbc.Col(html.Strong(f"{section_name}  "), width="auto"),
                dbc.Col(dbc.Badge(str(count), color="secondary"), width="auto"),
            ], className="g-1 align-items-center"),
            className="py-2",
        ),
        dbc.ListGroup(items or [dbc.ListGroupItem("Nenhuma tarefa nesta seção.", className="text-muted")],
                      flush=True),
    ], className="mb-3")


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = dbc.Container(
    [
        dcc.Store(id="tasks-refresh-store", data=0),
        dcc.Store(id="tasks-del-id-store"),
        add_modal,
        edit_modal,
        delete_modal,
        detail_offcanvas,

        # Header
        dbc.Row([
            dbc.Col(html.H2("Tarefas"), md=6),
            dbc.Col(
                html.Div([
                    dbc.Switch(id="tasks-show-done", label="Mostrar concluídas", value=False, className="me-3"),
                    dbc.Select(
                        id="tasks-priority-filter",
                        options=[
                            {"label": "Todas prioridades", "value": "all"},
                            {"label": "🚩 Prioridade 1", "value": "1"},
                            {"label": "🔶 Prioridade 2", "value": "2"},
                            {"label": "🔷 Prioridade 3", "value": "3"},
                            {"label": "⬜ Sem prioridade", "value": "4"},
                        ],
                        value="all",
                        style={"maxWidth": "200px"},
                    ),
                    dbc.Button(
                        [html.I(className="bi bi-plus-circle me-2"), "Nova Tarefa"],
                        id="tasks-open-add-btn",
                        color="primary",
                        className="ms-3",
                    ),
                ], className="d-flex align-items-center justify-content-end"),
                md=6,
            ),
        ], className="mb-4 mt-2 align-items-center"),

        # Sections
        html.Div(id="tasks-board"),

        # Notification toast
        dbc.Toast(
            id="tasks-toast",
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
# Helper: load all tasks as nested dicts
# ---------------------------------------------------------------------------

def load_tasks_tree(session, priority_filter="all"):
    from app.database import Task, Client, TaskLabel

    client_map = {c.id: c.name for c in session.query(Client).all()}

    query = session.query(Task).filter(Task.parent_id.is_(None))
    if priority_filter != "all":
        query = query.filter(Task.priority == int(priority_filter))
    root_tasks = query.order_by(Task.priority, Task.due_date, Task.created_at).all()

    def to_dict(t):
        subs = [to_dict(s) for s in sorted(t.subtasks, key=lambda x: (x.priority, x.created_at))]
        label_data = [{"id": lb.id, "name": lb.name, "color": lb.color} for lb in t.labels]
        return {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "source": t.source,
            "priority": t.priority,
            "section": t.section or "Para fazer",
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "deadline": t.deadline.isoformat() if t.deadline else None,
            "client_id": t.client_id,
            "client": client_map.get(t.client_id) if t.client_id else None,
            "recurrence": t.recurrence or "",
            "recurrence_end": t.recurrence_end.isoformat() if t.recurrence_end else None,
            "subtasks": subs,
            "subtask_count": len(subs),
            "labels": label_data,
        }

    return [to_dict(t) for t in root_tasks], client_map


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("tasks-board", "children"),
    Input("tasks-refresh-store", "data"),
    Input("tasks-show-done", "value"),
    Input("tasks-priority-filter", "value"),
)
def render_board(_refresh, show_done, priority_filter):
    from app.database import get_session

    with get_session() as session:
        tasks, client_map = load_tasks_tree(session, priority_filter)

    # Group by section
    sections: dict[str, list] = {s: [] for s in DEFAULT_SECTIONS}
    for t in tasks:
        sec = t["section"] if t["section"] in sections else "Para fazer"
        sections[sec].append(t)

    return [render_section(name, items, client_map, show_done) for name, items in sections.items()]


# Toggle task status via checkbox
@callback(
    Output("tasks-refresh-store", "data", allow_duplicate=True),
    Output("tasks-toast", "children", allow_duplicate=True),
    Output("tasks-toast", "header", allow_duplicate=True),
    Output("tasks-toast", "is_open", allow_duplicate=True),
    Input({"type": "task-check", "index": ALL}, "value"),
    State({"type": "task-check", "index": ALL}, "id"),
    State("tasks-refresh-store", "data"),
    prevent_initial_call=True,
)
def toggle_task_status(check_values, check_ids, refresh):
    if not ctx.triggered_id:
        return no_update, no_update, no_update, no_update

    triggered = ctx.triggered_id
    task_id = triggered["index"]
    # find which checkbox
    checked = next((v for v, i in zip(check_values, check_ids) if i["index"] == task_id), [])
    new_status = "done" if task_id in (checked or []) else "pending"

    from app.database import get_session, Task, complete_recurring_task

    with get_session() as session:
        task = session.get(Task, task_id)
        if task:
            if new_status == "done" and task.recurrence:
                created_next = complete_recurring_task(task_id, session)
                if created_next:
                    msg = "Tarefa concluída! Próxima ocorrência criada. 🔁"
                else:
                    msg = "Tarefa concluída! ✓"
            else:
                task.status = new_status
                task.completed_at = datetime.utcnow() if new_status == "done" else None
                msg = "Tarefa concluída! ✓" if new_status == "done" else "Tarefa reaberta."

    return (refresh or 0) + 1, msg, "Tarefas", True


# Open add modal
@callback(
    Output("tasks-add-modal", "is_open"),
    Input("tasks-open-add-btn", "n_clicks"),
    Input("tasks-add-cancel", "n_clicks"),
    State("tasks-add-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_add_modal(_open, _cancel, is_open):
    return not is_open


# Load client/parent/label options into add modal
@callback(
    Output("tasks-add-client", "options"),
    Output("tasks-add-parent", "options"),
    Output("tasks-add-labels", "options"),
    Input("tasks-add-modal", "is_open"),
)
def load_add_options(is_open):
    if not is_open:
        return [], [], []
    from app.database import get_session, Client, Task, TaskLabel

    with get_session() as session:
        clients = [{"label": c.name, "value": c.id} for c in session.query(Client).filter_by(status="active").all()]
        parents = [{"label": f"[{t.id}] {t.title}", "value": t.id} for t in session.query(Task).filter(Task.parent_id.is_(None)).all()]
        labels = [{"label": lb.name, "value": lb.id} for lb in session.query(TaskLabel).order_by(TaskLabel.name).all()]
    return clients, parents, labels


# NLP auto-parse callback for add modal title
@callback(
    Output("tasks-add-nlp-preview", "children"),
    Output("tasks-add-due", "value"),
    Output("tasks-add-priority", "value"),
    Output("tasks-add-start-time", "value"),
    Output("tasks-add-duration", "value"),
    Input("tasks-add-title", "value"),
    prevent_initial_call=True,
)
def parse_add_title(text):
    from app.services.nlp_task import parse_task_text
    if not text or not text.strip():
        return "", no_update, no_update, no_update, no_update
    p = parse_task_text(text)
    preview = _nlp_preview(p)
    due = p["due_date"].isoformat() if p["due_date"] else no_update
    prio = p["priority"] if p["priority"] < 4 else no_update
    start = p["start_time"] if p["start_time"] else no_update
    dur = str(p["duration_minutes"]) if p["duration_minutes"] else no_update
    return preview, due, prio, start, dur


# NLP auto-parse callback for edit modal title
@callback(
    Output("tasks-edit-nlp-preview", "children"),
    Output("tasks-edit-due", "value", allow_duplicate=True),
    Output("tasks-edit-priority", "value", allow_duplicate=True),
    Output("tasks-edit-start-time", "value"),
    Output("tasks-edit-duration", "value"),
    Input("tasks-edit-title", "value"),
    prevent_initial_call=True,
)
def parse_edit_title(text):
    from app.services.nlp_task import parse_task_text
    if not text or not text.strip():
        return "", no_update, no_update, no_update, no_update
    p = parse_task_text(text)
    preview = _nlp_preview(p)
    due = p["due_date"].isoformat() if p["due_date"] else no_update
    prio = p["priority"] if p["priority"] < 4 else no_update
    start = p["start_time"] if p["start_time"] else no_update
    dur = str(p["duration_minutes"]) if p["duration_minutes"] else no_update
    return preview, due, prio, start, dur


def _nlp_preview(p):
    """Render a compact preview of parsed NLP fields."""
    parts = []
    if p["due_date"]:
        parts.append(dbc.Badge(f"📅 {p['due_date'].strftime('%d/%m')}", color="info", className="me-1"))
    if p["start_time"]:
        parts.append(dbc.Badge(f"🕐 {p['start_time']}", color="secondary", className="me-1"))
    if p["duration_minutes"]:
        h, m = divmod(p["duration_minutes"], 60)
        dur_str = f"{h}h{m:02d}" if m else f"{h}h" if h else f"{p['duration_minutes']}min"
        parts.append(dbc.Badge(f"⏱ {dur_str}", color="secondary", className="me-1"))
    prio_map = {1: ("P1", "danger"), 2: ("P2", "warning"), 3: ("P3", "primary")}
    if p["priority"] in prio_map:
        lbl, col = prio_map[p["priority"]]
        parts.append(dbc.Badge(lbl, color=col, className="me-1"))
    return html.Div(parts) if parts else ""


# Save new task
@callback(
    Output("tasks-add-alert", "children"),
    Output("tasks-add-alert", "is_open"),
    Output("tasks-add-modal", "is_open", allow_duplicate=True),
    Output("tasks-refresh-store", "data", allow_duplicate=True),
    Input("tasks-add-save", "n_clicks"),
    State("tasks-add-title", "value"),
    State("tasks-add-desc", "value"),
    State("tasks-add-section", "value"),
    State("tasks-add-priority", "value"),
    State("tasks-add-due", "value"),
    State("tasks-add-deadline", "value"),
    State("tasks-add-start-time", "value"),
    State("tasks-add-duration", "value"),
    State("tasks-add-client", "value"),
    State("tasks-add-parent", "value"),
    State("tasks-add-recurrence", "value"),
    State("tasks-add-recurrence-end", "value"),
    State("tasks-add-labels", "value"),
    State("tasks-refresh-store", "data"),
    prevent_initial_call=True,
)
def save_new_task(_n, title, desc, section, priority, due, deadline, start_time, duration, client_id, parent_id, recurrence, recurrence_end, label_ids, refresh):
    if not title or not title.strip():
        return "Título é obrigatório.", True, no_update, no_update

    from app.database import get_session, Task, TaskLabelAssoc
    from app.services.nlp_task import parse_task_text

    # Strip NLP tokens from title before saving
    parsed = parse_task_text(title.strip())
    clean_title = parsed["title"] or title.strip()

    try:
        with get_session() as session:
            task = Task(
                title=clean_title,
                description=desc.strip() if desc else None,
                section=section or "Para fazer",
                priority=int(priority) if priority else 4,
                due_date=date.fromisoformat(due) if due else None,
                deadline=date.fromisoformat(deadline) if deadline else None,
                start_time=start_time if start_time else None,
                duration_minutes=int(duration) if duration else None,
                client_id=int(client_id) if client_id else None,
                parent_id=int(parent_id) if parent_id else None,
                recurrence=recurrence if recurrence else None,
                recurrence_end=date.fromisoformat(recurrence_end) if recurrence_end else None,
                status="pending",
                source="manual",
                created_at=datetime.utcnow(),
            )
            session.add(task)
            session.flush()  # get task.id
            if label_ids:
                for lid in label_ids:
                    session.add(TaskLabelAssoc(task_id=task.id, label_id=int(lid)))
        return no_update, False, False, (refresh or 0) + 1
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update


# Open edit modal and populate fields
@callback(
    Output("tasks-edit-modal", "is_open"),
    Output("tasks-edit-id-store", "data"),
    Output("tasks-edit-title", "value"),
    Output("tasks-edit-desc", "value"),
    Output("tasks-edit-section", "value"),
    Output("tasks-edit-priority", "value"),
    Output("tasks-edit-due", "value"),
    Output("tasks-edit-deadline", "value"),
    Output("tasks-edit-start-time", "value", allow_duplicate=True),
    Output("tasks-edit-duration", "value", allow_duplicate=True),
    Output("tasks-edit-client", "value"),
    Output("tasks-edit-client", "options"),
    Output("tasks-edit-recurrence", "value"),
    Output("tasks-edit-recurrence-end", "value"),
    Output("tasks-edit-labels", "value"),
    Output("tasks-edit-labels", "options"),
    Input({"type": "task-edit-btn", "index": ALL}, "n_clicks"),
    Input("tasks-edit-cancel", "n_clicks"),
    State("tasks-edit-modal", "is_open"),
    prevent_initial_call=True,
)
def open_edit_modal(edit_clicks, _cancel, is_open):
    triggered = ctx.triggered_id
    no_vals = (False,) + (no_update,) * 15
    if triggered == "tasks-edit-cancel" or not any(edit_clicks):
        return no_vals

    task_id = triggered["index"]

    from app.database import get_session, Task, Client, TaskLabel

    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            return no_vals
        clients = [{"label": c.name, "value": c.id} for c in session.query(Client).filter_by(status="active").all()]
        all_labels = [{"label": lb.name, "value": lb.id} for lb in session.query(TaskLabel).order_by(TaskLabel.name).all()]
        selected_label_ids = [lb.id for lb in task.labels]
        dur_val = str(task.duration_minutes) if task.duration_minutes else ""
        return (
            True,
            task_id,
            task.title,
            task.description or "",
            task.section or "Para fazer",
            task.priority or 4,
            task.due_date.isoformat() if task.due_date else None,
            task.deadline.isoformat() if task.deadline else None,
            task.start_time or "",
            dur_val,
            task.client_id,
            clients,
            task.recurrence or "",
            task.recurrence_end.isoformat() if task.recurrence_end else None,
            selected_label_ids,
            all_labels,
        )


# Save edited task
@callback(
    Output("tasks-edit-alert", "children"),
    Output("tasks-edit-alert", "is_open"),
    Output("tasks-edit-modal", "is_open", allow_duplicate=True),
    Output("tasks-refresh-store", "data", allow_duplicate=True),
    Input("tasks-edit-save", "n_clicks"),
    State("tasks-edit-id-store", "data"),
    State("tasks-edit-title", "value"),
    State("tasks-edit-desc", "value"),
    State("tasks-edit-section", "value"),
    State("tasks-edit-priority", "value"),
    State("tasks-edit-due", "value"),
    State("tasks-edit-deadline", "value"),
    State("tasks-edit-start-time", "value"),
    State("tasks-edit-duration", "value"),
    State("tasks-edit-client", "value"),
    State("tasks-edit-recurrence", "value"),
    State("tasks-edit-recurrence-end", "value"),
    State("tasks-edit-labels", "value"),
    State("tasks-refresh-store", "data"),
    prevent_initial_call=True,
)
def save_edited_task(_n, task_id, title, desc, section, priority, due, deadline, start_time, duration, client_id, recurrence, recurrence_end, label_ids, refresh):
    if not title or not title.strip():
        return "Título é obrigatório.", True, no_update, no_update

    from app.database import get_session, Task, TaskLabelAssoc
    from app.services.nlp_task import parse_task_text

    # Strip NLP tokens from title before saving
    parsed = parse_task_text(title.strip())
    clean_title = parsed["title"] or title.strip()

    try:
        with get_session() as session:
            task = session.get(Task, task_id)
            if not task:
                return "Tarefa não encontrada.", True, no_update, no_update
            task.title = clean_title
            task.description = desc.strip() if desc else None
            task.section = section or "Para fazer"
            task.priority = int(priority) if priority else 4
            task.due_date = date.fromisoformat(due) if due else None
            task.deadline = date.fromisoformat(deadline) if deadline else None
            task.start_time = start_time if start_time else None
            task.duration_minutes = int(duration) if duration else None
            task.client_id = int(client_id) if client_id else None
            task.recurrence = recurrence if recurrence else None
            task.recurrence_end = date.fromisoformat(recurrence_end) if recurrence_end else None
            # Update labels: remove old, add new
            session.query(TaskLabelAssoc).filter_by(task_id=task.id).delete()
            session.flush()
            if label_ids:
                for lid in label_ids:
                    session.add(TaskLabelAssoc(task_id=task.id, label_id=int(lid)))
        return no_update, False, False, (refresh or 0) + 1
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update


# Open delete modal
@callback(
    Output("tasks-del-modal", "is_open"),
    Output("tasks-del-id-store", "data"),
    Input({"type": "task-del-btn", "index": ALL}, "n_clicks"),
    Input("tasks-del-cancel", "n_clicks"),
    State("tasks-del-modal", "is_open"),
    prevent_initial_call=True,
)
def open_delete_modal(del_clicks, _cancel, is_open):
    triggered = ctx.triggered_id
    if triggered == "tasks-del-cancel" or not any(del_clicks):
        return False, no_update
    return True, triggered["index"]


# Confirm delete
@callback(
    Output("tasks-del-modal", "is_open", allow_duplicate=True),
    Output("tasks-refresh-store", "data", allow_duplicate=True),
    Output("tasks-toast", "children"),
    Output("tasks-toast", "header"),
    Output("tasks-toast", "is_open"),
    Input("tasks-del-confirm", "n_clicks"),
    State("tasks-del-id-store", "data"),
    State("tasks-refresh-store", "data"),
    prevent_initial_call=True,
)
def confirm_delete(_n, task_id, refresh):
    if not task_id:
        return False, no_update, no_update, no_update, no_update

    from app.database import get_session, Task

    with get_session() as session:
        task = session.get(Task, task_id)
        if task:
            session.delete(task)
    return False, (refresh or 0) + 1, "Tarefa excluída.", "Tarefas", True


# Open task detail offcanvas when task title is clicked
@callback(
    Output("tasks-detail-offcanvas", "is_open"),
    Output("tasks-detail-task-id", "data"),
    Input({"type": "task-title-btn", "index": ALL}, "n_clicks"),
    State("tasks-detail-offcanvas", "is_open"),
    prevent_initial_call=True,
)
def open_task_detail(title_clicks, is_open):
    triggered = ctx.triggered_id
    if not triggered or not any(c for c in title_clicks if c):
        return no_update, no_update
    task_id = triggered["index"]
    return True, task_id


# Load task details into offcanvas
@callback(
    Output("tasks-detail-content", "children"),
    Output("tasks-comments-list", "children"),
    Input("tasks-detail-task-id", "data"),
    Input("tasks-refresh-store", "data"),
    prevent_initial_call=True,
)
def load_task_details(task_id, _refresh):
    if not task_id:
        return no_update, no_update

    from app.database import get_session, Task, Client

    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            return html.P("Tarefa não encontrada."), html.Div()

        client_name = None
        if task.client_id:
            client = session.get(Client, task.client_id)
            client_name = client.name if client else None

        label_badges = [
            dbc.Badge(
                lb.name,
                style={"backgroundColor": lb.color, "color": "#fff"},
                className="me-1",
            )
            for lb in task.labels
        ]

        recurrence_label = RECURRENCE_LABELS.get(task.recurrence or "", task.recurrence or "Sem recorrência")

        detail_items = [
            html.H5(task.title, className="mb-2"),
        ]
        if task.description:
            detail_items.append(html.P(task.description, className="text-muted"))

        info_rows = []
        if client_name:
            info_rows.append(html.Tr([html.Td(html.Strong("Cliente:")), html.Td(client_name)]))
        if task.due_date:
            info_rows.append(html.Tr([html.Td(html.Strong("Vencimento:")), html.Td(task.due_date.isoformat())]))
        if task.deadline:
            info_rows.append(html.Tr([html.Td(html.Strong("Prazo:")), html.Td(task.deadline.isoformat())]))
        if task.recurrence:
            info_rows.append(html.Tr([html.Td(html.Strong("Recorrência:")), html.Td([html.Span("🔁 "), recurrence_label])]))
        if task.recurrence_end:
            info_rows.append(html.Tr([html.Td(html.Strong("Fim recorrência:")), html.Td(task.recurrence_end.isoformat())]))

        status_color = "success" if task.status == "done" else "warning"
        info_rows.append(html.Tr([
            html.Td(html.Strong("Status:")),
            html.Td(dbc.Badge("Concluída" if task.status == "done" else "Pendente", color=status_color)),
        ]))

        if info_rows:
            detail_items.append(html.Table(info_rows, className="table table-sm table-borderless"))

        if label_badges:
            detail_items.append(html.Div([html.Strong("Etiquetas: ")] + label_badges, className="mt-2"))

        # Comments
        comment_items = []
        for c in task.comments:
            comment_items.append(
                dbc.Card(
                    dbc.CardBody([
                        html.P(c.content, className="mb-1"),
                        html.Small(
                            c.created_at.strftime("%d/%m/%Y %H:%M") if c.created_at else "",
                            className="text-muted",
                        ),
                    ]),
                    className="mb-2",
                )
            )

        comments_div = html.Div(comment_items) if comment_items else html.P("Nenhum comentário ainda.", className="text-muted")

    return html.Div(detail_items), comments_div


# Save new comment
@callback(
    Output("tasks-comment-input", "value"),
    Output("tasks-refresh-store", "data", allow_duplicate=True),
    Input("tasks-comment-submit", "n_clicks"),
    State("tasks-detail-task-id", "data"),
    State("tasks-comment-input", "value"),
    State("tasks-refresh-store", "data"),
    prevent_initial_call=True,
)
def save_comment(_n, task_id, content, refresh):
    if not task_id or not content or not content.strip():
        return no_update, no_update

    from app.database import get_session, TaskComment

    with get_session() as session:
        comment = TaskComment(
            task_id=task_id,
            content=content.strip(),
            created_at=datetime.utcnow(),
        )
        session.add(comment)

    return "", (refresh or 0) + 1
