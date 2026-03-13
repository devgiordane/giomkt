"""Today page – lista + timeline de horas do dia."""

from datetime import date, datetime, timedelta

import dash
from dash import html, dcc, callback, Output, Input, State, no_update, ctx
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/today", name="Hoje")

PRIORITY_COLORS  = {1: "danger",  2: "warning", 3: "primary", 4: "secondary"}
PRIORITY_ICONS   = {1: "bi bi-flag-fill text-danger", 2: "bi bi-flag-fill text-warning",
                    3: "bi bi-flag-fill text-primary", 4: "bi bi-flag text-secondary"}
PRIORITY_LABELS  = {1: "Prioridade 1", 2: "Prioridade 2", 3: "Prioridade 3", 4: "Sem prioridade"}
WEEKDAY_FULL     = ["Segunda-feira","Terça-feira","Quarta-feira","Quinta-feira","Sexta-feira","Sábado","Domingo"]
MONTH_PT         = ["","janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]

DURATION_OPTIONS = [
    {"label": "15 min",  "value": 15},
    {"label": "30 min",  "value": 30},
    {"label": "45 min",  "value": 45},
    {"label": "1 hora",  "value": 60},
    {"label": "1h 30min","value": 90},
    {"label": "2 horas", "value": 120},
    {"label": "3 horas", "value": 180},
    {"label": "4 horas", "value": 240},
]

TIMELINE_START = 6   # 06:00
TIMELINE_END   = 23  # 23:00
HOUR_PX        = 60  # pixels per hour


# ---------------------------------------------------------------------------
# Task row (list view)
# ---------------------------------------------------------------------------

def _time_label(start_time, duration_minutes):
    if not start_time:
        return None
    try:
        h, m = map(int, start_time.split(":"))
        start_dt = datetime(2000, 1, 1, h, m)
        if duration_minutes:
            end_dt = start_dt + timedelta(minutes=int(duration_minutes))
            return f"{start_time} – {end_dt.strftime('%H:%M')} ({duration_minutes}min)"
        return start_time
    except Exception:
        return start_time


def render_task_row(t: dict, show_postpone=True) -> html.Div:
    is_done    = t["status"] == "done"
    priority   = t.get("priority", 4)
    flag_cls   = PRIORITY_ICONS.get(priority, PRIORITY_ICONS[4])
    pcolor     = PRIORITY_COLORS.get(priority, "secondary")
    deadline   = t.get("deadline")
    today_str  = date.today().isoformat()
    overdue_dl = deadline and deadline < today_str and not is_done
    time_lbl   = _time_label(t.get("start_time"), t.get("duration_minutes"))

    badges = []
    if time_lbl:
        badges.append(dbc.Badge([html.I(className="bi bi-clock me-1"), time_lbl],
                                color="dark", className="me-1 fw-normal"))
    if t.get("client"):
        badges.append(dbc.Badge(t["client"], color="info", className="me-1 fw-normal"))
    if t.get("section"):
        badges.append(dbc.Badge(t["section"], color="secondary", className="me-1 fw-normal"))
    if deadline:
        badges.append(dbc.Badge(f"Prazo {deadline}",
                                color="danger" if overdue_dl else "light",
                                text_color=None if overdue_dl else "dark",
                                className="me-1 fw-normal"))
    if t.get("subtask_count", 0) > 0:
        done_s = t.get("done_subtasks", 0)
        total_s = t["subtask_count"]
        badges.append(dbc.Badge(f"{done_s}/{total_s} subtarefas",
                                color="success" if done_s == total_s else "secondary",
                                className="me-1 fw-normal"))

    actions = [
        dbc.Button(html.I(className="bi bi-flag-fill"),
                   id={"type": "today-priority-btn", "index": t["id"]},
                   color=pcolor, size="sm", outline=True,
                   className="me-1 py-0 px-1", title=PRIORITY_LABELS.get(priority),
                   style={"fontSize": "0.7rem"}),
        dbc.Button([html.I(className="bi bi-clock me-1"), "Tempo"],
                   id={"type": "today-time-btn", "index": t["id"]},
                   color="outline-secondary", size="sm",
                   className="me-1 py-0 px-2", title="Definir horário e duração",
                   style={"fontSize": "0.75rem"}),
    ]
    if show_postpone:
        actions.append(dbc.Button([html.I(className="bi bi-arrow-right me-1"), "Amanhã"],
                                  id={"type": "today-postpone-btn", "index": t["id"]},
                                  color="outline-secondary", size="sm",
                                  className="me-1 py-0 px-2",
                                  style={"fontSize": "0.75rem"}))
    actions.append(dbc.Button(html.I(className="bi bi-pencil"),
                              id={"type": "today-edit-btn", "index": t["id"]},
                              color="link", size="sm", className="p-0 text-secondary",
                              style={"fontSize": "0.8rem"}))

    return html.Div(
        dbc.Row([
            dbc.Col(dbc.Checklist(
                options=[{"label": "", "value": t["id"]}],
                value=[t["id"]] if is_done else [],
                id={"type": "today-check", "index": t["id"]},
                inline=True, style={"marginTop": "2px"}),
                width="auto"),
            dbc.Col(html.I(className=flag_cls, style={"fontSize": "0.9rem"}), width="auto"),
            dbc.Col([
                html.Span(t["title"], style={
                    "textDecoration": "line-through" if is_done else "none",
                    "color": "#888" if is_done else "inherit",
                    "fontWeight": "500"}),
                html.Div(badges, className="mt-1") if badges else None,
            ]),
            dbc.Col(html.Div(actions, className="d-flex align-items-center today-actions"),
                    width="auto"),
        ], align="center", className="g-2 py-2"),
        className="border-bottom today-task-row px-2",
    )


# ---------------------------------------------------------------------------
# Timeline view
# ---------------------------------------------------------------------------

TIMELINE_COLORS = {1: "#dc3545", 2: "#fd7e14", 3: "#0d6efd", 4: "#6c757d"}


def render_timeline(tasks: list) -> html.Div:
    total_hours = TIMELINE_END - TIMELINE_START
    total_px    = total_hours * HOUR_PX
    now         = datetime.now()
    now_offset  = (now.hour - TIMELINE_START) * HOUR_PX + (now.minute / 60) * HOUR_PX

    # Hour labels + grid lines
    hour_labels = []
    grid_lines  = []
    for h in range(TIMELINE_START, TIMELINE_END + 1):
        top = (h - TIMELINE_START) * HOUR_PX
        hour_labels.append(
            html.Div(f"{h:02d}:00", style={
                "position": "absolute", "top": f"{top - 8}px",
                "right": "8px", "fontSize": "0.7rem", "color": "#6c757d",
                "lineHeight": "1",
            })
        )
        grid_lines.append(
            html.Div(style={
                "position": "absolute", "top": f"{top}px",
                "left": "0", "right": "0", "height": "1px",
                "background": "rgba(255,255,255,0.07)",
            })
        )

    # Half-hour faint lines
    for h in range(TIMELINE_START, TIMELINE_END):
        top = (h - TIMELINE_START) * HOUR_PX + HOUR_PX // 2
        grid_lines.append(html.Div(style={
            "position": "absolute", "top": f"{top}px",
            "left": "0", "right": "0", "height": "1px",
            "background": "rgba(255,255,255,0.03)",
        }))

    # Current time indicator
    now_line = []
    if TIMELINE_START <= now.hour < TIMELINE_END:
        now_line = [
            html.Div(style={
                "position": "absolute", "top": f"{now_offset}px",
                "left": "0", "right": "0", "height": "2px",
                "background": "#ff4444", "zIndex": 10,
            }),
            html.Div(style={
                "position": "absolute", "top": f"{now_offset - 5}px",
                "left": "-5px", "width": "10px", "height": "10px",
                "borderRadius": "50%", "background": "#ff4444", "zIndex": 11,
            }),
        ]

    # Task blocks — group overlapping by column
    timed = []
    for t in tasks:
        if not t.get("start_time"):
            continue
        try:
            h, m    = map(int, t["start_time"].split(":"))
            dur     = int(t.get("duration_minutes") or 30)
            top_px  = (h - TIMELINE_START) * HOUR_PX + (m / 60) * HOUR_PX
            h_px    = max((dur / 60) * HOUR_PX, 20)
            timed.append({**t, "_top": top_px, "_height": h_px,
                          "_end_min": h * 60 + m + dur})
        except Exception:
            continue

    # Simple column assignment to avoid overlap
    timed.sort(key=lambda x: x["_top"])
    columns: list[int] = []  # end_min per column
    for t in timed:
        start_min = int(t["_top"] / HOUR_PX * 60) + TIMELINE_START * 60
        placed = False
        for ci, end in enumerate(columns):
            if start_min >= end:
                columns[ci] = t["_end_min"]
                t["_col"] = ci
                placed = True
                break
        if not placed:
            t["_col"] = len(columns)
            columns.append(t["_end_min"])

    num_cols = max((t["_col"] for t in timed), default=-1) + 1 or 1
    col_w    = 100 / num_cols

    task_blocks = []
    for t in timed:
        is_done  = t["status"] == "done"
        pcolor   = TIMELINE_COLORS.get(t.get("priority", 4), TIMELINE_COLORS[4])
        col_idx  = t["_col"]
        dur      = int(t.get("duration_minutes") or 30)
        h2, m2   = map(int, t["start_time"].split(":"))
        end_dt   = datetime(2000,1,1,h2,m2) + timedelta(minutes=dur)
        time_str = f"{t['start_time']} – {end_dt.strftime('%H:%M')}"

        task_blocks.append(
            html.Div(
                [
                    html.Div(t["title"], style={
                        "fontWeight": "600", "fontSize": "0.78rem",
                        "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap",
                        "textDecoration": "line-through" if is_done else "none",
                        "opacity": "0.6" if is_done else "1",
                    }),
                    html.Div(time_str, style={"fontSize": "0.68rem", "opacity": "0.8"}),
                ],
                id={"type": "today-time-btn", "index": t["id"]},
                n_clicks=0,
                style={
                    "position": "absolute",
                    "top":    f"{t['_top']}px",
                    "height": f"{t['_height'] - 3}px",
                    "left":   f"calc({col_idx * col_w}% + 2px)",
                    "width":  f"calc({col_w}% - 4px)",
                    "background": pcolor,
                    "opacity": "0.85",
                    "borderRadius": "4px",
                    "padding": "3px 6px",
                    "cursor": "pointer",
                    "overflow": "hidden",
                    "zIndex": 5,
                    "boxSizing": "border-box",
                },
            )
        )

    task_area = html.Div(
        task_blocks + grid_lines + now_line,
        style={
            "position": "absolute", "top": "0", "left": "0",
            "right": "0", "bottom": "0",
        },
    )

    return html.Div([
        # Left: hour labels
        html.Div(
            hour_labels,
            style={
                "position": "absolute", "top": "0", "left": "0",
                "width": "48px", "height": f"{total_px}px",
            },
        ),
        # Right: grid + tasks
        html.Div(
            task_area,
            style={
                "position": "absolute", "top": "0",
                "left": "52px", "right": "0",
                "height": f"{total_px}px",
            },
        ),
    ], style={
        "position": "relative",
        "height": f"{total_px}px",
        "minHeight": f"{total_px}px",
        "overflow": "hidden",
    })


# ---------------------------------------------------------------------------
# Modals
# ---------------------------------------------------------------------------

time_modal = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle("Horário e duração")),
    dbc.ModalBody([
        dcc.Store(id="today-time-task-id"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Hora de início"),
                dbc.Input(id="today-time-start", type="time", step=900),  # 15min steps
            ], md=6, className="mb-3"),
            dbc.Col([
                dbc.Label("Duração"),
                dbc.Select(
                    id="today-time-duration",
                    options=DURATION_OPTIONS,
                    value=30,
                ),
            ], md=6, className="mb-3"),
        ]),
        html.Div(id="today-time-preview", className="text-muted", style={"fontSize": "0.85rem"}),
    ]),
    dbc.ModalFooter([
        dbc.Button("Limpar", id="today-time-clear", color="outline-danger", className="me-auto"),
        dbc.Button("Cancelar", id="today-time-cancel", color="secondary", className="me-2"),
        dbc.Button("Salvar", id="today-time-save", color="primary"),
    ]),
], id="today-time-modal", is_open=False)

priority_modal = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle("Alterar prioridade")),
    dbc.ModalBody([
        dcc.Store(id="today-priority-task-id"),
        dbc.RadioItems(
            id="today-priority-select",
            options=[
                {"label": html.Span([html.I(className="bi bi-flag-fill text-danger me-2"), "Prioridade 1 (Alta)"], className="d-flex align-items-center"), "value": 1},
                {"label": html.Span([html.I(className="bi bi-flag-fill text-warning me-2"), "Prioridade 2"], className="d-flex align-items-center"), "value": 2},
                {"label": html.Span([html.I(className="bi bi-flag-fill text-primary me-2"), "Prioridade 3"], className="d-flex align-items-center"), "value": 3},
                {"label": html.Span([html.I(className="bi bi-flag text-secondary me-2"), "Sem prioridade"], className="d-flex align-items-center"), "value": 4},
            ],
            value=4,
        ),
    ]),
    dbc.ModalFooter([
        dbc.Button("Cancelar", id="today-priority-cancel", color="secondary", className="me-2"),
        dbc.Button("Salvar", id="today-priority-save", color="primary"),
    ]),
], id="today-priority-modal", is_open=False)

postpone_modal = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle("Adiar tarefa")),
    dbc.ModalBody([
        dcc.Store(id="today-postpone-task-id"),
        dbc.Label("Nova data de vencimento"),
        dbc.Input(id="today-postpone-date", type="date",
                  value=(date.today() + timedelta(days=1)).isoformat()),
    ]),
    dbc.ModalFooter([
        dbc.Button("Cancelar", id="today-postpone-cancel", color="secondary", className="me-2"),
        dbc.Button("Amanhã", id="today-postpone-tomorrow", color="outline-primary", className="me-2"),
        dbc.Button("Salvar", id="today-postpone-save", color="primary"),
    ]),
], id="today-postpone-modal", is_open=False)

add_task_modal = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle("Nova tarefa para hoje")),
    dbc.ModalBody([
        dbc.Alert(id="today-add-alert", is_open=False, color="danger"),
        dbc.Row([dbc.Col([dbc.Label("Título *"), dbc.Input(id="today-add-title", placeholder="O que precisa ser feito?")], className="mb-3")]),
        dbc.Row([dbc.Col([dbc.Label("Descrição"), dbc.Textarea(id="today-add-desc", rows=2)], className="mb-3")]),
        dbc.Row([
            dbc.Col([dbc.Label("Prioridade"),
                     dbc.Select(id="today-add-priority",
                                options=[{"label":"🚩 P1","value":1},{"label":"🔶 P2","value":2},
                                         {"label":"🔷 P3","value":3},{"label":"⬜ Nenhuma","value":4}],
                                value=4)], md=4, className="mb-3"),
            dbc.Col([dbc.Label("Hora de início"), dbc.Input(id="today-add-start", type="time", step=900)], md=4, className="mb-3"),
            dbc.Col([dbc.Label("Duração"), dbc.Select(id="today-add-duration", options=DURATION_OPTIONS, value=30)], md=4, className="mb-3"),
        ]),
        dbc.Row([
            dbc.Col([dbc.Label("Prazo final"), dbc.Input(id="today-add-deadline", type="date")], md=6, className="mb-3"),
            dbc.Col([dbc.Label("Cliente"), dcc.Dropdown(id="today-add-client", clearable=True)], md=6, className="mb-3"),
        ]),
    ]),
    dbc.ModalFooter([
        dbc.Button("Cancelar", id="today-add-cancel", color="secondary", className="me-2"),
        dbc.Button("Adicionar", id="today-add-save", color="primary"),
    ]),
], id="today-add-modal", is_open=False, size="lg")


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = dbc.Container([
    dcc.Store(id="today-refresh", data=0),
    time_modal, priority_modal, postpone_modal, add_task_modal,

    # Header
    dbc.Row([
        dbc.Col([
            html.H2(id="today-title", className="mb-0"),
            html.Div(id="today-subtitle", className="text-muted", style={"fontSize": "0.85rem"}),
        ], md=5),
        dbc.Col(
            html.Div([
                dbc.Select(id="today-group-by",
                           options=[{"label":"Por prioridade","value":"priority"},
                                    {"label":"Por seção","value":"section"},
                                    {"label":"Por cliente","value":"client"},
                                    {"label":"Sem agrupamento","value":"none"}],
                           value="priority",
                           style={"maxWidth":"180px","fontSize":"0.85rem"}),
                dbc.Switch(id="today-show-done", label="Concluídas", value=False, className="ms-3"),
                dbc.Button([html.I(className="bi bi-plus-circle me-1"), "Nova tarefa"],
                           id="today-open-add", color="primary", size="sm", className="ms-3"),
            ], className="d-flex align-items-center justify-content-end"),
            md=7,
        ),
    ], className="mb-3 mt-2 align-items-center"),

    # Progress
    html.Div(id="today-progress-area", className="mb-3"),

    # Two-column: list + timeline
    dbc.Row([
        # Left — task list
        dbc.Col(
            dbc.Card(dbc.CardBody(html.Div(id="today-task-list"), className="p-2")),
            md=7,
        ),
        # Right — timeline
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(
                    dbc.Row([
                        dbc.Col(html.Strong("Timeline do dia"), width="auto"),
                        dbc.Col(
                            html.Small("Clique em uma tarefa para editar horário", className="text-muted"),
                            className="ms-2 d-flex align-items-center",
                        ),
                    ], className="g-1 align-items-center"),
                    className="py-2",
                ),
                dbc.CardBody(
                    html.Div(id="today-timeline", style={"overflowY": "auto", "maxHeight": "640px"}),
                    className="p-2",
                ),
            ]),
        ], md=5),
    ], className="mb-3"),

    # Overdue
    html.Div(id="today-overdue-section"),

    dbc.Toast(id="today-toast", header="Hoje", is_open=False, dismissable=True, duration=3000,
              style={"position":"fixed","bottom":"1rem","right":"1rem","zIndex":9999}),
], fluid=True)


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------

def _load_today_tasks():
    from app.database import get_session, Task, Client
    today = date.today()
    with get_session() as session:
        client_map = {c.id: c.name for c in session.query(Client).all()}
        today_tasks = (session.query(Task)
                       .filter(Task.due_date == today, Task.parent_id.is_(None))
                       .order_by(Task.priority, Task.start_time, Task.created_at).all())
        overdue_tasks = (session.query(Task)
                         .filter(Task.due_date < today, Task.status == "pending",
                                 Task.parent_id.is_(None))
                         .order_by(Task.due_date, Task.priority).all())

        def to_dict(t):
            done_subs = sum(1 for s in t.subtasks if s.status == "done")
            return {
                "id": t.id, "title": t.title, "status": t.status,
                "priority": t.priority or 4, "section": t.section or "Para fazer",
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "deadline": t.deadline.isoformat() if t.deadline else None,
                "start_time": t.start_time, "duration_minutes": t.duration_minutes,
                "client": client_map.get(t.client_id) if t.client_id else None,
                "client_id": t.client_id,
                "subtask_count": len(t.subtasks), "done_subtasks": done_subs,
            }
        return [to_dict(t) for t in today_tasks], [to_dict(t) for t in overdue_tasks]


def _apply_sort_group(tasks, group_by, show_done):
    visible = tasks if show_done else [t for t in tasks if t["status"] != "done"]

    def group_render(label, items, color="secondary"):
        if not items:
            return html.Div()
        return html.Div([
            html.Div([dbc.Badge(label, color=color, className="me-2"),
                      html.Span(f"{len(items)}", className="text-muted", style={"fontSize":"0.8rem"})],
                     className="d-flex align-items-center mb-1 mt-3"),
            html.Div([render_task_row(t) for t in items]),
        ])

    if group_by == "priority":
        groups = {1:[], 2:[], 3:[], 4:[]}
        for t in visible:
            groups[t.get("priority", 4)].append(t)
        clr = {1:"danger", 2:"warning", 3:"primary", 4:"secondary"}
        return html.Div([group_render(PRIORITY_LABELS[p], groups[p], clr[p]) for p in [1,2,3,4]])

    if group_by == "section":
        groups: dict = {}
        for t in visible:
            groups.setdefault(t.get("section") or "Para fazer", []).append(t)
        return html.Div([group_render(s, items) for s, items in groups.items()])

    if group_by == "client":
        groups: dict = {}
        for t in visible:
            groups.setdefault(t.get("client") or "Sem cliente", []).append(t)
        return html.Div([group_render(c, items, "info") for c, items in groups.items()])

    return html.Div([render_task_row(t) for t in visible] or [
        html.P("Nenhuma tarefa para hoje.", className="text-muted text-center py-4")
    ])


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("today-title", "children"),
    Output("today-subtitle", "children"),
    Output("today-progress-area", "children"),
    Output("today-task-list", "children"),
    Output("today-timeline", "children"),
    Output("today-overdue-section", "children"),
    Input("today-refresh", "data"),
    Input("today-group-by", "value"),
    Input("today-show-done", "value"),
)
def render_today(_refresh, group_by, show_done):
    today   = date.today()
    weekday = WEEKDAY_FULL[today.weekday()]
    subtitle = f"{weekday}, {today.day} de {MONTH_PT[today.month]} de {today.year}"

    today_tasks, overdue_tasks = _load_today_tasks()

    total = len(today_tasks)
    done  = sum(1 for t in today_tasks if t["status"] == "done")
    pct   = int(done / total * 100) if total else 0
    progress = html.Div([
        dbc.Row([
            dbc.Col(html.Span(f"{done}/{total} concluídas", className="text-muted",
                              style={"fontSize":"0.85rem"}), width="auto"),
            dbc.Col(html.Span(f"{pct}%", className="text-muted ms-1",
                              style={"fontSize":"0.85rem"}), width="auto"),
        ], className="g-0 mb-1"),
        dbc.Progress(value=pct, color="success" if pct == 100 else "primary",
                     style={"height":"6px"}),
    ]) if total else None

    task_list = _apply_sort_group(today_tasks, group_by, show_done)
    timeline  = render_timeline(today_tasks)

    overdue_section = None
    if overdue_tasks:
        overdue_section = dbc.Card([
            dbc.CardHeader(dbc.Row([
                dbc.Col(html.Strong("Atrasadas"), width="auto"),
                dbc.Col(dbc.Badge(str(len(overdue_tasks)), color="danger"), width="auto"),
                dbc.Col(dbc.Button("Reagendar para hoje", id="today-reschedule-all",
                                   color="outline-warning", size="sm"),
                        className="ms-auto", width="auto"),
            ], align="center", className="g-2"), className="py-2"),
            dbc.CardBody(html.Div([render_task_row(t, show_postpone=False)
                                   for t in overdue_tasks]), className="p-2"),
        ], className="mb-3 border-danger")

    return "Hoje", subtitle, progress, task_list, timeline, overdue_section


# Toggle done
@callback(
    Output("today-refresh", "data", allow_duplicate=True),
    Output("today-toast", "children", allow_duplicate=True),
    Output("today-toast", "is_open", allow_duplicate=True),
    Input({"type": "today-check", "index": dash.ALL}, "value"),
    State({"type": "today-check", "index": dash.ALL}, "id"),
    State("today-refresh", "data"),
    prevent_initial_call=True,
)
def toggle_done(check_values, check_ids, refresh):
    triggered = ctx.triggered_id
    if not triggered:
        return no_update, no_update, no_update
    task_id = triggered["index"]
    checked = next((v for v, i in zip(check_values, check_ids) if i["index"] == task_id), [])
    new_status = "done" if task_id in (checked or []) else "pending"
    from app.database import get_session, Task
    with get_session() as session:
        task = session.get(Task, task_id)
        if task:
            task.status = new_status
            task.completed_at = datetime.utcnow() if new_status == "done" else None
    msg = "✓ Concluída! Ótimo trabalho." if new_status == "done" else "Tarefa reaberta."
    return (refresh or 0) + 1, msg, True


# Open time modal (from list button OR timeline block click)
@callback(
    Output("today-time-modal", "is_open"),
    Output("today-time-task-id", "data"),
    Output("today-time-start", "value"),
    Output("today-time-duration", "value"),
    Input({"type": "today-time-btn", "index": dash.ALL}, "n_clicks"),
    Input("today-time-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def open_time_modal(clicks, _cancel):
    triggered = ctx.triggered_id
    if triggered == "today-time-cancel" or not any(c for c in clicks if c):
        return False, no_update, no_update, no_update
    task_id = triggered["index"]
    from app.database import get_session, Task
    with get_session() as session:
        task = session.get(Task, task_id)
        start = task.start_time or ""
        dur   = task.duration_minutes or 30
    return True, task_id, start, dur


# Preview in time modal
@callback(
    Output("today-time-preview", "children"),
    Input("today-time-start", "value"),
    Input("today-time-duration", "value"),
)
def preview_time(start, duration):
    if not start:
        return "Sem horário definido"
    try:
        h, m   = map(int, start.split(":"))
        dur    = int(duration or 30)
        end_dt = datetime(2000,1,1,h,m) + timedelta(minutes=dur)
        return f"⏱ {start} → {end_dt.strftime('%H:%M')}  ({dur} min)"
    except Exception:
        return ""


# Save time
@callback(
    Output("today-time-modal", "is_open", allow_duplicate=True),
    Output("today-refresh", "data", allow_duplicate=True),
    Output("today-toast", "children"),
    Output("today-toast", "is_open"),
    Input("today-time-save", "n_clicks"),
    Input("today-time-clear", "n_clicks"),
    State("today-time-task-id", "data"),
    State("today-time-start", "value"),
    State("today-time-duration", "value"),
    State("today-refresh", "data"),
    prevent_initial_call=True,
)
def save_time(save_n, clear_n, task_id, start, duration, refresh):
    if not task_id:
        return False, no_update, no_update, no_update
    from app.database import get_session, Task
    clearing = ctx.triggered_id == "today-time-clear"
    with get_session() as session:
        task = session.get(Task, task_id)
        if task:
            task.start_time        = None if clearing else (start or None)
            task.duration_minutes  = None if clearing else (int(duration) if duration else None)
    msg = "Horário removido." if clearing else f"Horário salvo: {start}  ({duration}min)."
    return False, (refresh or 0) + 1, msg, True


# Priority modal
@callback(
    Output("today-priority-modal", "is_open"),
    Output("today-priority-task-id", "data"),
    Output("today-priority-select", "value"),
    Input({"type": "today-priority-btn", "index": dash.ALL}, "n_clicks"),
    Input("today-priority-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def open_priority(clicks, _cancel):
    triggered = ctx.triggered_id
    if triggered == "today-priority-cancel" or not any(c for c in clicks if c):
        return False, no_update, no_update
    task_id = triggered["index"]
    from app.database import get_session, Task
    with get_session() as session:
        task = session.get(Task, task_id)
        cur  = task.priority if task else 4
    return True, task_id, cur


@callback(
    Output("today-priority-modal", "is_open", allow_duplicate=True),
    Output("today-refresh", "data", allow_duplicate=True),
    Output("today-toast", "children", allow_duplicate=True),
    Output("today-toast", "is_open", allow_duplicate=True),
    Input("today-priority-save", "n_clicks"),
    State("today-priority-task-id", "data"),
    State("today-priority-select", "value"),
    State("today-refresh", "data"),
    prevent_initial_call=True,
)
def save_priority(_n, task_id, priority, refresh):
    if not task_id:
        return False, no_update, no_update, no_update
    from app.database import get_session, Task
    with get_session() as session:
        task = session.get(Task, task_id)
        if task:
            task.priority = int(priority)
    return False, (refresh or 0) + 1, f"Prioridade: {PRIORITY_LABELS.get(priority)}.", True


# Postpone modal
@callback(
    Output("today-postpone-modal", "is_open"),
    Output("today-postpone-task-id", "data"),
    Output("today-postpone-date", "value"),
    Input({"type": "today-postpone-btn", "index": dash.ALL}, "n_clicks"),
    Input("today-postpone-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def open_postpone(clicks, _cancel):
    triggered = ctx.triggered_id
    if triggered == "today-postpone-cancel" or not any(c for c in clicks if c):
        return False, no_update, no_update
    return True, triggered["index"], (date.today() + timedelta(days=1)).isoformat()


@callback(
    Output("today-postpone-modal", "is_open", allow_duplicate=True),
    Output("today-refresh", "data", allow_duplicate=True),
    Output("today-toast", "children", allow_duplicate=True),
    Output("today-toast", "is_open", allow_duplicate=True),
    Input("today-postpone-save", "n_clicks"),
    Input("today-postpone-tomorrow", "n_clicks"),
    State("today-postpone-task-id", "data"),
    State("today-postpone-date", "value"),
    State("today-refresh", "data"),
    prevent_initial_call=True,
)
def save_postpone(save_n, tmr_n, task_id, custom_date, refresh):
    if not task_id:
        return False, no_update, no_update, no_update
    new_date = (date.today() + timedelta(days=1)) if ctx.triggered_id == "today-postpone-tomorrow" \
               else date.fromisoformat(custom_date)
    from app.database import get_session, Task
    with get_session() as session:
        task = session.get(Task, task_id)
        if task:
            task.due_date = new_date
    return False, (refresh or 0) + 1, f"Adiada para {new_date.strftime('%d/%m/%Y')}.", True


# Reschedule overdue
@callback(
    Output("today-refresh", "data", allow_duplicate=True),
    Output("today-toast", "children", allow_duplicate=True),
    Output("today-toast", "is_open", allow_duplicate=True),
    Input("today-reschedule-all", "n_clicks"),
    State("today-refresh", "data"),
    prevent_initial_call=True,
)
def reschedule_all(_n, refresh):
    from app.database import get_session, Task
    today = date.today()
    with get_session() as session:
        overdue = session.query(Task).filter(Task.due_date < today, Task.status == "pending").all()
        count = len(overdue)
        for t in overdue:
            t.due_date = today
    return (refresh or 0) + 1, f"{count} tarefa(s) reagendada(s) para hoje.", True


# Add modal
@callback(
    Output("today-add-modal", "is_open"),
    Output("today-add-client", "options"),
    Input("today-open-add", "n_clicks"),
    Input("today-add-cancel", "n_clicks"),
    State("today-add-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_add(_open, _cancel, is_open):
    if ctx.triggered_id == "today-open-add":
        from app.database import get_session, Client
        with get_session() as session:
            clients = [{"label": c.name, "value": c.id}
                       for c in session.query(Client).filter_by(status="active").all()]
        return True, clients
    return False, no_update


@callback(
    Output("today-add-alert", "children"),
    Output("today-add-alert", "is_open"),
    Output("today-add-modal", "is_open", allow_duplicate=True),
    Output("today-refresh", "data", allow_duplicate=True),
    Input("today-add-save", "n_clicks"),
    State("today-add-title", "value"),
    State("today-add-desc", "value"),
    State("today-add-priority", "value"),
    State("today-add-start", "value"),
    State("today-add-duration", "value"),
    State("today-add-deadline", "value"),
    State("today-add-client", "value"),
    State("today-refresh", "data"),
    prevent_initial_call=True,
)
def save_add(_n, title, desc, priority, start, duration, deadline, client_id, refresh):
    if not title or not title.strip():
        return "Título é obrigatório.", True, no_update, no_update
    from app.database import get_session, Task
    try:
        with get_session() as session:
            task = Task(
                title=title.strip(),
                description=desc.strip() if desc else None,
                priority=int(priority) if priority else 4,
                due_date=date.today(),
                start_time=start or None,
                duration_minutes=int(duration) if duration else None,
                deadline=date.fromisoformat(deadline) if deadline else None,
                client_id=int(client_id) if client_id else None,
                status="pending", source="manual", section="Para fazer",
                created_at=datetime.utcnow(),
            )
            session.add(task)
        return no_update, False, False, (refresh or 0) + 1
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update
