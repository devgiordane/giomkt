"""Tasks page – Todoist-inspired task management."""

from datetime import date, datetime

import dash
from dash import html, dcc, callback, Output, Input, State, no_update, ctx
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

# ---------------------------------------------------------------------------
# Modals
# ---------------------------------------------------------------------------

def make_task_modal(modal_id, title_text):
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle(title_text)),
            dbc.ModalBody(
                [
                    dbc.Alert(id=f"{modal_id}-alert", is_open=False, color="danger"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Título *"),
                            dbc.Input(id=f"{modal_id}-title", placeholder="O que precisa ser feito?"),
                        ], className="mb-3"),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Descrição"),
                            dbc.Textarea(id=f"{modal_id}-desc", placeholder="Detalhes opcionais", rows=2),
                        ], className="mb-3"),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Seção"),
                            dbc.Select(
                                id=f"{modal_id}-section",
                                options=[{"label": s, "value": s} for s in DEFAULT_SECTIONS],
                                value="Para fazer",
                            ),
                        ], md=6, className="mb-3"),
                        dbc.Col([
                            dbc.Label("Prioridade"),
                            dbc.Select(
                                id=f"{modal_id}-priority",
                                options=PRIORITY_OPTIONS,
                                value=4,
                            ),
                        ], md=6, className="mb-3"),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Data de Vencimento"),
                            dbc.Input(id=f"{modal_id}-due", type="date"),
                        ], md=6, className="mb-3"),
                        dbc.Col([
                            dbc.Label("Prazo Final (Deadline)"),
                            dbc.Input(id=f"{modal_id}-deadline", type="date"),
                        ], md=6, className="mb-3"),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Cliente (opcional)"),
                            dcc.Dropdown(id=f"{modal_id}-client", placeholder="Selecione um cliente", clearable=True),
                        ], className="mb-3"),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Subtarefa de (opcional)"),
                            dcc.Dropdown(id=f"{modal_id}-parent", placeholder="Tarefa pai", clearable=True),
                        ], className="mb-3"),
                    ]),
                ]
            ),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id=f"{modal_id}-cancel", color="secondary", className="me-2"),
                dbc.Button("Salvar", id=f"{modal_id}-save", color="primary"),
            ]),
        ],
        id=f"{modal_id}-modal",
        is_open=False,
        size="lg",
    )


add_modal = make_task_modal("tasks-add", "Nova Tarefa")

# Edit modal (same structure, different IDs)
edit_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Editar Tarefa")),
        dbc.ModalBody(
            [
                dcc.Store(id="tasks-edit-id-store"),
                dbc.Alert(id="tasks-edit-alert", is_open=False, color="danger"),
                dbc.Row([dbc.Col([dbc.Label("Título *"), dbc.Input(id="tasks-edit-title")], className="mb-3")]),
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
                dbc.Row([dbc.Col([dbc.Label("Cliente"), dcc.Dropdown(id="tasks-edit-client", clearable=True)], className="mb-3")]),
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
                html.Span(
                    task["title"],
                    style={
                        "textDecoration": "line-through" if is_done else "none",
                        "color": "#888" if is_done else "inherit",
                        "fontWeight": "500",
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
    from app.database import Task, Client

    client_map = {c.id: c.name for c in session.query(Client).all()}

    query = session.query(Task).filter(Task.parent_id.is_(None))
    if priority_filter != "all":
        query = query.filter(Task.priority == int(priority_filter))
    root_tasks = query.order_by(Task.priority, Task.due_date, Task.created_at).all()

    def to_dict(t):
        subs = [to_dict(s) for s in sorted(t.subtasks, key=lambda x: (x.priority, x.created_at))]
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
            "subtasks": subs,
            "subtask_count": len(subs),
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
    Input({"type": "task-check", "index": dash.ALL}, "value"),
    State({"type": "task-check", "index": dash.ALL}, "id"),
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

    from app.database import get_session, Task

    with get_session() as session:
        task = session.get(Task, task_id)
        if task:
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


# Load client/parent options into add modal
@callback(
    Output("tasks-add-client", "options"),
    Output("tasks-add-parent", "options"),
    Input("tasks-add-modal", "is_open"),
)
def load_add_options(is_open):
    if not is_open:
        return [], []
    from app.database import get_session, Client, Task

    with get_session() as session:
        clients = [{"label": c.name, "value": c.id} for c in session.query(Client).filter_by(status="active").all()]
        parents = [{"label": f"[{t.id}] {t.title}", "value": t.id} for t in session.query(Task).filter(Task.parent_id.is_(None)).all()]
    return clients, parents


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
    State("tasks-add-client", "value"),
    State("tasks-add-parent", "value"),
    State("tasks-refresh-store", "data"),
    prevent_initial_call=True,
)
def save_new_task(_n, title, desc, section, priority, due, deadline, client_id, parent_id, refresh):
    if not title or not title.strip():
        return "Título é obrigatório.", True, no_update, no_update

    from app.database import get_session, Task

    try:
        with get_session() as session:
            task = Task(
                title=title.strip(),
                description=desc.strip() if desc else None,
                section=section or "Para fazer",
                priority=int(priority) if priority else 4,
                due_date=date.fromisoformat(due) if due else None,
                deadline=date.fromisoformat(deadline) if deadline else None,
                client_id=int(client_id) if client_id else None,
                parent_id=int(parent_id) if parent_id else None,
                status="pending",
                source="manual",
                created_at=datetime.utcnow(),
            )
            session.add(task)
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
    Output("tasks-edit-client", "value"),
    Output("tasks-edit-client", "options"),
    Input({"type": "task-edit-btn", "index": dash.ALL}, "n_clicks"),
    Input("tasks-edit-cancel", "n_clicks"),
    State("tasks-edit-modal", "is_open"),
    prevent_initial_call=True,
)
def open_edit_modal(edit_clicks, _cancel, is_open):
    triggered = ctx.triggered_id
    if triggered == "tasks-edit-cancel" or not any(edit_clicks):
        return False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

    task_id = triggered["index"]

    from app.database import get_session, Task, Client

    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            return False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        clients = [{"label": c.name, "value": c.id} for c in session.query(Client).filter_by(status="active").all()]
        return (
            True,
            task_id,
            task.title,
            task.description or "",
            task.section or "Para fazer",
            task.priority or 4,
            task.due_date.isoformat() if task.due_date else None,
            task.deadline.isoformat() if task.deadline else None,
            task.client_id,
            clients,
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
    State("tasks-edit-client", "value"),
    State("tasks-refresh-store", "data"),
    prevent_initial_call=True,
)
def save_edited_task(_n, task_id, title, desc, section, priority, due, deadline, client_id, refresh):
    if not title or not title.strip():
        return "Título é obrigatório.", True, no_update, no_update

    from app.database import get_session, Task

    try:
        with get_session() as session:
            task = session.get(Task, task_id)
            if not task:
                return "Tarefa não encontrada.", True, no_update, no_update
            task.title = title.strip()
            task.description = desc.strip() if desc else None
            task.section = section or "Para fazer"
            task.priority = int(priority) if priority else 4
            task.due_date = date.fromisoformat(due) if due else None
            task.deadline = date.fromisoformat(deadline) if deadline else None
            task.client_id = int(client_id) if client_id else None
        return no_update, False, False, (refresh or 0) + 1
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update


# Open delete modal
@callback(
    Output("tasks-del-modal", "is_open"),
    Output("tasks-del-id-store", "data"),
    Input({"type": "task-del-btn", "index": dash.ALL}, "n_clicks"),
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
