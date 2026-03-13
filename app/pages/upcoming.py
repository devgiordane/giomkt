"""Upcoming page – lista semanal e calendário mensal de tarefas."""

from datetime import date, timedelta
import calendar as cal_mod

import dash
from dash import html, dcc, callback, Output, Input, State, no_update, ctx
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/upcoming", name="Em breve")

WEEKDAY_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
MONTH_PT = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]
MONTH_SHORT = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

PRIORITY_COLORS = {1: "danger", 2: "warning", 3: "primary", 4: "secondary"}
PRIORITY_ICONS = {
    1: "bi bi-flag-fill text-danger",
    2: "bi bi-flag-fill text-warning",
    3: "bi bi-flag-fill text-primary",
    4: "bi bi-flag text-secondary",
}


def week_start(ref: date) -> date:
    return ref - timedelta(days=ref.weekday())


# ---------------------------------------------------------------------------
# List view helpers
# ---------------------------------------------------------------------------

def render_task_row_list(t: dict) -> dbc.ListGroupItem:
    is_done = t["status"] == "done"
    priority = t.get("priority", 4)
    flag_cls = PRIORITY_ICONS.get(priority, PRIORITY_ICONS[4])
    deadline = t.get("deadline")
    today_str = date.today().isoformat()
    overdue = deadline and deadline < today_str and not is_done

    badges = []
    if t.get("client"):
        badges.append(dbc.Badge(t["client"], color="info", className="me-1"))
    if t.get("section"):
        badges.append(dbc.Badge(t["section"], color="secondary", className="me-1"))
    if deadline:
        badges.append(dbc.Badge(
            f"Prazo {deadline}",
            color="danger" if overdue else "light",
            text_color=None if overdue else "dark",
            className="me-1",
        ))
    if t.get("subtask_count", 0) > 0:
        badges.append(dbc.Badge(f"{t['subtask_count']} sub", color="secondary", className="me-1"))

    return dbc.ListGroupItem(
        dbc.Row([
            dbc.Col(
                dbc.Checklist(
                    options=[{"label": "", "value": t["id"]}],
                    value=[t["id"]] if is_done else [],
                    id={"type": "upcoming-check", "index": t["id"]},
                    inline=True,
                ),
                width="auto",
            ),
            dbc.Col(html.I(className=flag_cls, style={"fontSize": "0.85rem"}), width="auto"),
            dbc.Col([
                html.Span(
                    t["title"],
                    style={
                        "textDecoration": "line-through" if is_done else "none",
                        "color": "#888" if is_done else "inherit",
                        "fontWeight": "500",
                    },
                ),
                html.Div(badges, className="mt-1") if badges else None,
            ]),
            dbc.Col(
                dbc.Button(
                    html.I(className="bi bi-arrow-right-circle"),
                    id={"type": "upcoming-reschedule", "index": t["id"]},
                    size="sm", color="link", className="p-0 text-secondary",
                    title="Reagendar",
                ),
                width="auto",
            ),
        ], align="center", className="g-2"),
        className="border-bottom py-2",
        style={"background": "transparent"},
    )


def render_day_column(d: date, tasks: list, today: date) -> dbc.Col:
    is_today = d == today
    is_past = d < today
    day_name = WEEKDAY_PT[d.weekday()]
    label = f"{day_name}, {d.day} {MONTH_SHORT[d.month]}"
    header_class = "text-primary fw-bold" if is_today else ("text-muted" if is_past else "")
    border_color = "rgba(78,115,223,0.5)" if is_today else "rgba(255,255,255,0.07)"
    bg = "rgba(78,115,223,0.04)" if is_today else ("rgba(0,0,0,0.15)" if is_past else "transparent")

    task_items = [render_task_row_list(t) for t in tasks]

    return dbc.Col(
        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.Span(label, className=header_class),
                    html.Span(" ●", className="text-primary ms-1", style={"fontSize": "0.5rem", "verticalAlign": "middle"}) if is_today else None,
                ], className="d-flex align-items-center", style={"fontSize": "0.8rem", "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                className="py-2 px-3",
            ),
            dbc.ListGroup(
                task_items if task_items else [
                    dbc.ListGroupItem(
                        html.Span("—", className="text-muted", style={"fontSize": "0.8rem"}),
                        className="border-0 py-2",
                        style={"background": "transparent"},
                    )
                ],
                flush=True,
            ),
        ], style={"border": f"1px solid {border_color}", "background": bg, "minHeight": "80px"}),
        md=True,
        className="px-1",
    )


# ---------------------------------------------------------------------------
# Calendar view helpers
# ---------------------------------------------------------------------------

def render_calendar_cell(d: date | None, tasks: list, today: date) -> html.Td:
    if d is None:
        return html.Td(style={"background": "rgba(0,0,0,0.1)", "border": "1px solid rgba(255,255,255,0.05)"})

    is_today = d == today
    is_past = d < today
    has_tasks = bool(tasks)

    bg = "rgba(78,115,223,0.08)" if is_today else ("rgba(0,0,0,0.15)" if is_past else "transparent")
    border = "1px solid rgba(78,115,223,0.4)" if is_today else "1px solid rgba(255,255,255,0.07)"

    task_chips = []
    for t in tasks[:3]:  # max 3 visible per cell
        pcolor = PRIORITY_COLORS.get(t.get("priority", 4), "secondary")
        is_done = t["status"] == "done"
        task_chips.append(
            dbc.Badge(
                t["title"][:22] + ("…" if len(t["title"]) > 22 else ""),
                color=pcolor,
                className="d-block text-start mb-1",
                id={"type": "upcoming-reschedule", "index": t["id"]},
                style={
                    "cursor": "pointer",
                    "textDecoration": "line-through" if is_done else "none",
                    "opacity": "0.5" if is_done else "1",
                    "fontSize": "0.7rem",
                    "whiteSpace": "normal",
                    "lineHeight": "1.2",
                },
            )
        )
    if len(tasks) > 3:
        task_chips.append(
            html.Div(
                f"+{len(tasks) - 3} mais",
                className="text-muted",
                style={"fontSize": "0.7rem"},
            )
        )

    dot = html.Span("●", className="text-primary ms-1", style={"fontSize": "0.4rem", "verticalAlign": "middle"}) if is_today else None

    return html.Td(
        [
            html.Div(
                [html.Span(str(d.day), className="fw-bold" if is_today else "text-muted" if is_past else ""), dot],
                className="d-flex align-items-center mb-1",
                style={"fontSize": "0.85rem"},
            ),
            html.Div(task_chips),
        ],
        style={
            "background": bg,
            "border": border,
            "verticalAlign": "top",
            "padding": "6px 8px",
            "width": "calc(100%/7)",
            "minHeight": "90px",
        },
    )


def render_calendar_month(year: int, month: int, tasks_by_date: dict, today: date) -> html.Table:
    # Build calendar grid (weeks, starting Monday)
    cal = cal_mod.monthcalendar(year, month)

    header_row = html.Tr([
        html.Th(d, style={"textAlign": "center", "padding": "4px", "fontSize": "0.8rem", "color": "#adb5bd"})
        for d in WEEKDAY_PT
    ])

    rows = [header_row]
    for week in cal:
        cells = []
        for day_num in week:
            if day_num == 0:
                cells.append(render_calendar_cell(None, [], today))
            else:
                d = date(year, month, day_num)
                cells.append(render_calendar_cell(d, tasks_by_date.get(d, []), today))
        rows.append(html.Tr(cells))

    return html.Table(
        html.Tbody(rows),
        style={"width": "100%", "borderCollapse": "collapse", "tableLayout": "fixed"},
    )


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = dbc.Container(
    [
        dcc.Store(id="upcoming-week-offset", data=0),
        dcc.Store(id="upcoming-month-offset", data=0),
        dcc.Store(id="upcoming-refresh", data=0),
        dcc.Store(id="upcoming-view-mode", data="week"),   # "week" | "month"

        # Header
        dbc.Row([
            dbc.Col(html.H2("Em breve"), md="auto"),
            dbc.Col(
                html.Div([
                    dbc.Button(html.I(className="bi bi-chevron-left"), id="upcoming-prev", color="outline-secondary", size="sm", className="me-1"),
                    dbc.Button("Hoje", id="upcoming-today-btn", color="outline-primary", size="sm", className="me-1"),
                    dbc.Button(html.I(className="bi bi-chevron-right"), id="upcoming-next", color="outline-secondary", size="sm"),
                ], className="d-flex align-items-center"),
                md="auto",
            ),
            dbc.Col(
                html.Div(id="upcoming-period-label", className="text-muted fw-semibold", style={"fontSize": "1rem"}),
                className="d-flex align-items-center px-2",
            ),
            dbc.Col(
                html.Div([
                    # View toggle
                    dbc.ButtonGroup([
                        dbc.Button([html.I(className="bi bi-list-task me-1"), "Semana"], id="upcoming-view-week", color="primary", size="sm", outline=False),
                        dbc.Button([html.I(className="bi bi-calendar3 me-1"), "Mês"], id="upcoming-view-month", color="primary", size="sm", outline=True),
                    ], className="me-3"),
                    dbc.Button(
                        [html.I(className="bi bi-exclamation-triangle me-1"), "Reagendar atrasadas"],
                        id="upcoming-reschedule-all-btn",
                        color="outline-warning", size="sm",
                    ),
                ], className="d-flex align-items-center justify-content-end"),
                className="d-flex align-items-center justify-content-end",
            ),
        ], className="mb-3 mt-2 align-items-center"),

        # Overdue banner
        html.Div(id="upcoming-overdue-banner"),

        # Main content area
        html.Div(id="upcoming-main-content"),

        # Reschedule modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Reagendar tarefa")),
            dbc.ModalBody([
                dcc.Store(id="upcoming-reschedule-task-id"),
                dbc.Label("Nova data de vencimento"),
                dbc.Input(id="upcoming-reschedule-date", type="date"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="upcoming-reschedule-cancel", color="secondary", className="me-2"),
                dbc.Button("Salvar", id="upcoming-reschedule-save", color="primary"),
            ]),
        ], id="upcoming-reschedule-modal", is_open=False),

        dbc.Toast(
            id="upcoming-toast",
            header="Em breve",
            is_open=False,
            dismissable=True,
            duration=3000,
            style={"position": "fixed", "bottom": "1rem", "right": "1rem", "zIndex": 9999},
        ),
    ],
    fluid=True,
)


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------

def _load_tasks_for_dates(start: date, end: date):
    from app.database import get_session, Task, Client

    with get_session() as session:
        client_map = {c.id: c.name for c in session.query(Client).all()}
        tasks = (
            session.query(Task)
            .filter(Task.due_date >= start, Task.due_date <= end)
            .order_by(Task.priority, Task.due_date, Task.created_at)
            .all()
        )

        def to_dict(t):
            return {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority or 4,
                "section": t.section,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "deadline": t.deadline.isoformat() if t.deadline else None,
                "client": client_map.get(t.client_id) if t.client_id else None,
                "subtask_count": len(t.subtasks),
            }

        by_date: dict[date, list] = {}
        for t in tasks:
            by_date.setdefault(t.due_date, []).append(to_dict(t))

        overdue = (
            session.query(Task)
            .filter(Task.due_date < start, Task.status == "pending")
            .order_by(Task.due_date, Task.priority)
            .all()
        )
        overdue_count = len(overdue)

    return by_date, overdue_count


# ---------------------------------------------------------------------------
# Callbacks — view mode toggle
# ---------------------------------------------------------------------------

@callback(
    Output("upcoming-view-mode", "data"),
    Output("upcoming-view-week", "outline"),
    Output("upcoming-view-month", "outline"),
    Input("upcoming-view-week", "n_clicks"),
    Input("upcoming-view-month", "n_clicks"),
    State("upcoming-view-mode", "data"),
    prevent_initial_call=True,
)
def toggle_view(_, __, current_mode):
    triggered = ctx.triggered_id
    if triggered == "upcoming-view-week":
        return "week", False, True
    return "month", True, False


# Navigation
@callback(
    Output("upcoming-week-offset", "data"),
    Output("upcoming-month-offset", "data"),
    Input("upcoming-prev", "n_clicks"),
    Input("upcoming-next", "n_clicks"),
    Input("upcoming-today-btn", "n_clicks"),
    State("upcoming-week-offset", "data"),
    State("upcoming-month-offset", "data"),
    State("upcoming-view-mode", "data"),
    prevent_initial_call=True,
)
def navigate(prev, nxt, today_btn, week_off, month_off, mode):
    triggered = ctx.triggered_id
    if triggered == "upcoming-today-btn":
        return 0, 0
    delta = -1 if triggered == "upcoming-prev" else 1
    if mode == "month":
        return week_off, (month_off or 0) + delta
    return (week_off or 0) + delta, month_off


# Main render
@callback(
    Output("upcoming-main-content", "children"),
    Output("upcoming-period-label", "children"),
    Output("upcoming-overdue-banner", "children"),
    Input("upcoming-view-mode", "data"),
    Input("upcoming-week-offset", "data"),
    Input("upcoming-month-offset", "data"),
    Input("upcoming-refresh", "data"),
)
def render_content(mode, week_off, month_off, _refresh):
    today = date.today()

    if mode == "month":
        # Calculate target month
        year, month = today.year, today.month
        offset = month_off or 0
        m = month + offset
        while m > 12:
            m -= 12
            year += 1
        while m < 1:
            m += 12
            year -= 1

        start = date(year, m, 1)
        last_day = cal_mod.monthrange(year, m)[1]
        end = date(year, m, last_day)

        by_date, overdue_count = _load_tasks_for_dates(start, end)
        label = f"{MONTH_PT[m]} {year}"
        content = dbc.Card(
            dbc.CardBody(render_calendar_month(year, m, by_date, today), className="p-2"),
            className="mt-1",
        )

    else:  # week
        mon = week_start(today) + timedelta(weeks=week_off or 0)
        days = [mon + timedelta(days=i) for i in range(7)]
        by_date, overdue_count = _load_tasks_for_dates(days[0], days[-1])
        label = f"{days[0].day} {MONTH_SHORT[days[0].month]} – {days[-1].day} {MONTH_SHORT[days[-1].month]} {days[-1].year}"
        content = dbc.Row(
            [render_day_column(d, by_date.get(d, []), today) for d in days],
            className="g-0 mt-1",
        )

    banner = dbc.Alert(
        [html.Strong(f"{overdue_count} tarefa(s) atrasada(s)  "), html.Span("— clique em 'Reagendar atrasadas' para mover para hoje.", className="text-muted")],
        color="warning", className="mb-3 py-2",
    ) if overdue_count > 0 else None

    return content, label, banner


# Toggle task done
@callback(
    Output("upcoming-refresh", "data", allow_duplicate=True),
    Output("upcoming-toast", "children", allow_duplicate=True),
    Output("upcoming-toast", "is_open", allow_duplicate=True),
    Input({"type": "upcoming-check", "index": dash.ALL}, "value"),
    State({"type": "upcoming-check", "index": dash.ALL}, "id"),
    State("upcoming-refresh", "data"),
    prevent_initial_call=True,
)
def toggle_task(check_values, check_ids, refresh):
    from datetime import datetime
    from app.database import get_session, Task

    triggered = ctx.triggered_id
    if not triggered:
        return no_update, no_update, no_update

    task_id = triggered["index"]
    checked = next((v for v, i in zip(check_values, check_ids) if i["index"] == task_id), [])
    new_status = "done" if task_id in (checked or []) else "pending"

    with get_session() as session:
        task = session.get(Task, task_id)
        if task:
            task.status = new_status
            task.completed_at = datetime.utcnow() if new_status == "done" else None

    msg = "Tarefa concluída! ✓" if new_status == "done" else "Tarefa reaberta."
    return (refresh or 0) + 1, msg, True


# Open reschedule modal
@callback(
    Output("upcoming-reschedule-modal", "is_open"),
    Output("upcoming-reschedule-task-id", "data"),
    Output("upcoming-reschedule-date", "value"),
    Input({"type": "upcoming-reschedule", "index": dash.ALL}, "n_clicks"),
    Input("upcoming-reschedule-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def open_reschedule(row_clicks, _cancel):
    triggered = ctx.triggered_id
    if triggered == "upcoming-reschedule-cancel" or not any(c for c in row_clicks if c):
        return False, no_update, no_update

    task_id = triggered["index"]
    from app.database import get_session, Task
    with get_session() as session:
        task = session.get(Task, task_id)
        default = (task.due_date + timedelta(weeks=1)).isoformat() if task and task.due_date else (date.today() + timedelta(weeks=1)).isoformat()

    return True, task_id, default


# Save reschedule
@callback(
    Output("upcoming-reschedule-modal", "is_open", allow_duplicate=True),
    Output("upcoming-refresh", "data", allow_duplicate=True),
    Output("upcoming-toast", "children"),
    Output("upcoming-toast", "is_open"),
    Input("upcoming-reschedule-save", "n_clicks"),
    State("upcoming-reschedule-task-id", "data"),
    State("upcoming-reschedule-date", "value"),
    State("upcoming-refresh", "data"),
    prevent_initial_call=True,
)
def save_reschedule(_n, task_id, new_date, refresh):
    if not task_id or not new_date:
        return False, no_update, no_update, no_update

    from app.database import get_session, Task
    with get_session() as session:
        task = session.get(Task, task_id)
        if task:
            task.due_date = date.fromisoformat(new_date)

    return False, (refresh or 0) + 1, "Tarefa reagendada.", True


# Reschedule all overdue to today
@callback(
    Output("upcoming-refresh", "data", allow_duplicate=True),
    Output("upcoming-toast", "children", allow_duplicate=True),
    Output("upcoming-toast", "is_open", allow_duplicate=True),
    Input("upcoming-reschedule-all-btn", "n_clicks"),
    State("upcoming-refresh", "data"),
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
