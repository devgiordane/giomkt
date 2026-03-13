from datetime import datetime

import dash
from dash import html, dcc, callback, clientside_callback, Output, Input, State, no_update, ctx
import dash_bootstrap_components as dbc


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def create_sidebar():
    nav_items = [
        {"label": "Dashboard", "href": "/", "icon": "bi bi-speedometer2"},
        {"label": "Clientes", "href": "/clients", "icon": "bi bi-people"},
        {"label": "Campanhas", "href": "/campaigns", "icon": "bi bi-megaphone"},
        {"label": "Hoje", "href": "/today", "icon": "bi bi-sun"},
        {"label": "Tarefas", "href": "/tasks", "icon": "bi bi-check2-square"},
        {"label": "Em breve", "href": "/upcoming", "icon": "bi bi-calendar-week"},
        {"label": "Etiquetas", "href": "/labels", "icon": "bi bi-tags"},
        {"label": "Notas", "href": "/notes", "icon": "bi bi-journal-text"},
        {"label": "Alertas", "href": "/alerts", "icon": "bi bi-bell"},
        {"label": "Regras de Alerta", "href": "/alerts/rules", "icon": "bi bi-sliders"},
        {"label": "Wiki", "href": "/wiki", "icon": "bi bi-book"},
        {"label": "WhatsApp", "href": "/settings/whatsapp", "icon": "bi bi-whatsapp"},
    ]

    nav_links = []
    for item in nav_items:
        nav_links.append(
            dbc.NavItem(
                dbc.NavLink(
                    [html.I(className=f"{item['icon']} me-2"), item["label"]],
                    href=item["href"],
                    active="exact",
                    className="py-2 px-3 mb-1",
                )
            )
        )

    sidebar = html.Div(
        [
            html.A(
                [html.I(className="bi bi-graph-up-arrow me-2"), "GioMkt"],
                href="/",
                className="sidebar-brand",
            ),
            dbc.Nav(nav_links, vertical=True, pills=True),
            # Keyboard shortcut hint at the bottom of sidebar
            html.Div(
                [html.Kbd("Q"), " Adicionar tarefa"],
                className="sidebar-shortcut-hint",
            ),
        ],
        id="sidebar",
    )
    return sidebar


# ---------------------------------------------------------------------------
# Quick Add modal
# ---------------------------------------------------------------------------

def _create_quick_add_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle([
                    html.I(className="bi bi-plus-circle me-2"),
                    "Adicionar tarefa",
                ]),
                close_button=True,
            ),
            dbc.ModalBody([
                # Highlight wrapper: overlay div behind the input shows colored tokens
                html.Div([
                    html.Div(id="quick-add-highlight", className="quick-add-highlight"),
                    dbc.Input(
                        id="quick-add-input",
                        placeholder="Adicionar tarefa… ex: Reunião p1 @marketing amanhã {30 de abril}",
                        type="text",
                        autofocus=True,
                        debounce=False,
                        className="quick-add-input",
                        n_submit=0,
                    ),
                ], className="quick-add-wrapper"),
                # Live preview
                html.Div(id="quick-add-preview", className="quick-add-preview mt-2"),
                # Alert for errors
                dbc.Alert(
                    id="quick-add-alert",
                    is_open=False,
                    color="danger",
                    dismissable=True,
                    className="mt-2 mb-0",
                ),
            ]),
            dbc.ModalFooter([
                dbc.Button(
                    "Cancelar",
                    id="quick-add-cancel",
                    color="secondary",
                    outline=True,
                    className="me-2",
                ),
                dbc.Button(
                    [html.I(className="bi bi-check2 me-1"), "Salvar"],
                    id="quick-add-save",
                    color="primary",
                    n_clicks=0,
                ),
            ]),
        ],
        id="quick-add-modal",
        is_open=False,
        centered=True,
        size="lg",
        backdrop=True,
        keyboard=True,
    )


# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------

def create_layout():
    sidebar = create_sidebar()
    content = html.Div(
        dash.page_container,
        id="page-content",
    )

    # Hidden button clicked by JS keydown listener to trigger server callback
    kb_btn = html.Button(
        id="quick-add-kb-btn",
        n_clicks=0,
        style={"display": "none"},
        **{"aria-hidden": "true"},
    )

    # One-shot interval that fires once on page load to register the JS listener
    init_interval = dcc.Interval(
        id="quick-add-init",
        interval=300,
        max_intervals=1,
    )

    # Store to signal pages that a new task was saved (pages can watch this)
    refresh_store = dcc.Store(id="quick-add-refresh", data=0)

    return dbc.Container(
        [
            sidebar,
            content,
            kb_btn,
            init_interval,
            refresh_store,
            _create_quick_add_modal(),
        ],
        fluid=True,
        className="p-0",
    )


# ---------------------------------------------------------------------------
# Clientside callback – highlight tokens in Quick Add input
# ---------------------------------------------------------------------------

clientside_callback(
    """
    function(value) {
        // Directly set innerHTML on the overlay div — bypasses Dash vDOM
        var overlay = document.getElementById('quick-add-highlight');
        if (!overlay) return window.dash_clientside.no_update;

        if (!value) { overlay.innerHTML = ''; return window.dash_clientside.no_update; }

        // Token patterns and their CSS classes (order matters: more specific first)
        var tokens = [
            { re: /\\bdepois\\s+de\\s+amanh[aã]\\b/gi, cls: 'qa-hl-date' },
            { re: /\\btoda?\\s+(?:segunda|ter[cç]a|quarta|quinta|sexta|s[aá]bado|domingo)\\b/gi, cls: 'qa-hl-date' },
            { re: /\\bpr[oó]xim[ao]\\s+(?:segunda|ter[cç]a|quarta|quinta|sexta|s[aá]bado|domingo)\\b/gi, cls: 'qa-hl-date' },
            { re: /\\b(?:diariamente|todo\\s+dia|dias?\\s+[uú]teis|mensalmente|todo\\s+m[eê]s)\\b/gi, cls: 'qa-hl-date' },
            { re: /\\bamanh[aã]\\b/gi, cls: 'qa-hl-date' },
            { re: /\\bhoje\\b/gi, cls: 'qa-hl-date' },
            { re: /\\b(?:segunda|ter[cç]a|quarta|quinta|sexta|s[aá]bado|domingo)\\b/gi, cls: 'qa-hl-date' },
            { re: /\\bdia\\s+\\d{1,2}\\b/gi, cls: 'qa-hl-date' },
            { re: /\\b\\d{1,2}\\/\\d{1,2}(?:\\/\\d{2,4})?\\b/g, cls: 'qa-hl-date' },
            { re: /\\b\\d{1,2}\\s+de\\s+(?:janeiro|fevereiro|mar[cç]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\\b/gi, cls: 'qa-hl-date' },
            { re: /\\bpor\\s+(?:\\d+h(?:\\s*\\d+\\s*min)?|\\d+\\s*min(?:utos?)?)\\b/gi, cls: 'qa-hl-time' },
            { re: /\\b(?:[aà]s?\\s+)?\\d{1,2}(?:h\\d{0,2}|:\\d{2})\\b/gi, cls: 'qa-hl-time' },
            { re: /\\bp([123])\\b/gi, cls: 'qa-hl-priority' },
            { re: /@[\\w\\u00C0-\\u024F\\-]+/g, cls: 'qa-hl-label' },
            { re: /\\{[^}]*\\}/g, cls: 'qa-hl-deadline' },
            { re: /\\/[\\w\\u00C0-\\u024F][\\w\\u00C0-\\u024F\\s]*/g, cls: 'qa-hl-section' },
        ];

        var ranges = [];
        tokens.forEach(function(tok) {
            tok.re.lastIndex = 0;
            var m;
            while ((m = tok.re.exec(value)) !== null) {
                var s = m.index, e = m.index + m[0].length;
                var overlap = ranges.some(function(r) { return s < r[1] && e > r[0]; });
                if (!overlap) ranges.push([s, e, tok.cls]);
            }
        });
        ranges.sort(function(a, b) { return a[0] - b[0]; });

        function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
        var html = '', pos = 0;
        ranges.forEach(function(r) {
            if (r[0] > pos) html += esc(value.slice(pos, r[0]));
            html += '<mark class="' + r[2] + '">' + esc(value.slice(r[0], r[1])) + '</mark>';
            pos = r[1];
        });
        if (pos < value.length) html += esc(value.slice(pos));
        html += '&nbsp;';

        overlay.innerHTML = html;
        return window.dash_clientside.no_update;
    }
    """,
    Output("quick-add-highlight", "style"),  # dummy output — we use side-effects
    Input("quick-add-input", "value"),
    prevent_initial_call=False,
)


# ---------------------------------------------------------------------------
# Clientside callback – register keyboard shortcut once
# ---------------------------------------------------------------------------

clientside_callback(
    """
    function(n_intervals) {
        if (!window._gioQAListener) {
            window._gioQAListener = true;
            document.addEventListener('keydown', function(e) {
                // Only fire on 'q' or 'Q'
                if (e.key !== 'q' && e.key !== 'Q') return;
                // Skip when user is typing in a field
                var active = document.activeElement;
                if (active) {
                    var tag = active.tagName.toUpperCase();
                    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
                    if (active.isContentEditable) return;
                }
                // Click the hidden button to trigger the Dash callback
                var btn = document.getElementById('quick-add-kb-btn');
                if (btn) btn.click();
            });
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("quick-add-kb-btn", "n_clicks"),
    Input("quick-add-init", "n_intervals"),
    prevent_initial_call=False,
)


# ---------------------------------------------------------------------------
# Server callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("quick-add-modal", "is_open"),
    Output("quick-add-input", "value"),
    Input("quick-add-kb-btn", "n_clicks"),
    Input("quick-add-cancel", "n_clicks"),
    State("quick-add-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_quick_add(kb_clicks, cancel_clicks, is_open):
    triggered = ctx.triggered_id
    if triggered == "quick-add-cancel":
        return False, ""
    if triggered == "quick-add-kb-btn" and kb_clicks:
        return True, ""
    return no_update, no_update


@callback(
    Output("quick-add-preview", "children"),
    Input("quick-add-input", "value"),
    prevent_initial_call=True,
)
def update_quick_add_preview(text):
    from app.services.nlp_task import parse_task_text

    if not text or not text.strip():
        return ""

    parsed = parse_task_text(text)
    parts = []

    if parsed["title"]:
        parts.append(
            html.Span(
                [html.I(className="bi bi-file-text me-1"), parsed["title"]],
                className="qa-preview-title",
            )
        )

    priority_badges = {
        1: ("P1", "danger"),
        2: ("P2", "warning"),
        3: ("P3", "primary"),
    }
    if parsed["priority"] in priority_badges:
        label, color = priority_badges[parsed["priority"]]
        parts.append(dbc.Badge(label, color=color, className="qa-preview-badge"))

    if parsed["due_date"]:
        parts.append(
            dbc.Badge(
                [html.I(className="bi bi-calendar-event me-1"),
                 parsed["due_date"].strftime("%d/%m/%Y")],
                color="info",
                className="qa-preview-badge",
            )
        )

    if parsed["deadline"]:
        parts.append(
            dbc.Badge(
                [html.I(className="bi bi-hourglass-split me-1"),
                 "Prazo: ", parsed["deadline"].strftime("%d/%m/%Y")],
                color="warning",
                className="qa-preview-badge",
            )
        )

    if parsed["recurrence"]:
        rec_label = {
            "daily": "Diário",
            "weekdays": "Dias úteis",
            "monthly": "Mensal",
        }.get(parsed["recurrence"], parsed["recurrence"])
        parts.append(
            dbc.Badge(
                [html.I(className="bi bi-arrow-repeat me-1"), rec_label],
                color="secondary",
                className="qa-preview-badge",
            )
        )

    for lname in parsed["label_names"]:
        parts.append(
            dbc.Badge(
                [html.I(className="bi bi-tag me-1"), lname],
                color="success",
                className="qa-preview-badge",
            )
        )

    if parsed["section"]:
        parts.append(
            dbc.Badge(
                [html.I(className="bi bi-folder me-1"), parsed["section"]],
                color="light",
                text_color="dark",
                className="qa-preview-badge",
            )
        )

    if not parts:
        return ""

    return html.Div(parts, className="d-flex flex-wrap gap-1 align-items-center")


@callback(
    Output("quick-add-alert", "children"),
    Output("quick-add-alert", "is_open"),
    Output("quick-add-modal", "is_open", allow_duplicate=True),
    Output("quick-add-input", "value", allow_duplicate=True),
    Output("quick-add-refresh", "data"),
    Input("quick-add-save", "n_clicks"),
    Input("quick-add-input", "n_submit"),
    State("quick-add-input", "value"),
    State("quick-add-refresh", "data"),
    prevent_initial_call=True,
)
def save_quick_add(_n_clicks, _n_submit, text, refresh_count):
    if not text or not text.strip():
        return "Digite o título da tarefa.", True, no_update, no_update, no_update

    from app.services.nlp_task import parse_task_text
    from app.database import get_session, Task, TaskLabel, TaskLabelAssoc

    parsed = parse_task_text(text.strip())
    if not parsed["title"]:
        return "Título não pode estar vazio.", True, no_update, no_update, no_update

    try:
        with get_session() as session:
            # Resolve label names to IDs
            label_ids = []
            for lname in parsed["label_names"]:
                lb = session.query(TaskLabel).filter(
                    TaskLabel.name.ilike(lname)
                ).first()
                if lb:
                    label_ids.append(lb.id)

            task = Task(
                title=parsed["title"],
                priority=parsed["priority"],
                due_date=parsed["due_date"],
                deadline=parsed["deadline"],
                recurrence=parsed["recurrence"] or None,
                section=parsed["section"] or "Para fazer",
                status="pending",
                source="manual",
                created_at=datetime.utcnow(),
            )
            session.add(task)
            session.flush()
            for lid in label_ids:
                session.add(TaskLabelAssoc(task_id=task.id, label_id=lid))

        new_refresh = (refresh_count or 0) + 1
        return no_update, False, False, "", new_refresh

    except Exception as exc:
        return f"Erro ao salvar: {exc}", True, no_update, no_update, no_update
