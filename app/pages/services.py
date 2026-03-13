"""Services/Domains management page."""

from datetime import date, timedelta

import dash
from dash import html, dcc, callback, Output, Input, State, no_update, ctx, ALL
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import plotly.graph_objects as go

dash.register_page(__name__, path="/services", name="Serviços")

SERVICE_TYPES = [
    {"label": "Domínio", "value": "dominio"},
    {"label": "Hospedagem", "value": "hospedagem"},
    {"label": "Servidor", "value": "servidor"},
    {"label": "API", "value": "api"},
    {"label": "Software", "value": "software"},
]

BILLING_CYCLES = [
    {"label": "Mensal", "value": "monthly"},
    {"label": "Anual", "value": "annual"},
]

TYPE_LABELS = {t["value"]: t["label"] for t in SERVICE_TYPES}


def _modal(prefix, title):
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(title)),
        dbc.ModalBody([
            dbc.Alert(id=f"{prefix}-alert", is_open=False, color="danger"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Nome *"),
                    dbc.Input(id=f"{prefix}-name"),
                ], md=6, className="mb-3"),
                dbc.Col([
                    dbc.Label("Tipo *"),
                    dcc.Dropdown(id=f"{prefix}-type", options=SERVICE_TYPES, clearable=False),
                ], md=6, className="mb-3"),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Cliente"),
                    dcc.Dropdown(id=f"{prefix}-client"),
                ], md=6, className="mb-3"),
                dbc.Col([
                    dbc.Label("Valor (R$)"),
                    dbc.Input(id=f"{prefix}-value", type="number", min=0, step=0.01),
                ], md=6, className="mb-3"),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Ciclo"),
                    dcc.Dropdown(id=f"{prefix}-cycle", options=BILLING_CYCLES, value="monthly", clearable=False),
                ], md=6, className="mb-3"),
                dbc.Col([
                    dbc.Label("Vencimento"),
                    dbc.Input(id=f"{prefix}-due", type="date"),
                ], md=6, className="mb-3"),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Observações"),
                    dbc.Textarea(id=f"{prefix}-notes", rows=2),
                ], className="mb-3"),
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id=f"{prefix}-cancel", color="secondary", className="me-2"),
            dbc.Button("Salvar", id=f"{prefix}-save", color="primary"),
        ]),
    ], id=f"{prefix}-modal", is_open=False, size="lg")


layout = dbc.Container([
    dcc.Store(id="svc-refresh", data=0),
    dcc.Store(id="svc-edit-id"),
    dcc.Store(id="svc-del-id"),

    _modal("svc-add", "Novo Serviço"),
    _modal("svc-edit", "Editar Serviço"),

    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Confirmar exclusão")),
        dbc.ModalBody("Tem certeza que deseja excluir este serviço?"),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="svc-del-cancel", color="secondary", className="me-2"),
            dbc.Button("Excluir", id="svc-del-confirm", color="danger"),
        ]),
    ], id="svc-del-modal", is_open=False),

    # Header
    dbc.Row([
        dbc.Col(html.H2([html.I(className="bi bi-hdd-rack me-2"), "Serviços"]), md=8),
        dbc.Col(
            dbc.Button([html.I(className="bi bi-plus-circle me-2"), "Novo Serviço"],
                       id="svc-open-add", color="primary"),
            md=4, className="text-end",
        ),
    ], className="mb-4 mt-2 align-items-center"),

    # KPIs
    html.Div(id="svc-kpis", className="mb-4"),

    # Chart + Table
    dbc.Row([
        dbc.Col(dcc.Graph(id="svc-chart", config={"displayModeBar": False}), md=4),
        dbc.Col(html.Div(id="svc-table"), md=8),
    ]),

    dbc.Toast(id="svc-toast", header="", is_open=False, dismissable=True, duration=3000,
              style={"position": "fixed", "bottom": "1rem", "right": "1rem", "zIndex": 9999}),
], fluid=True)


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

@callback(
    Output("svc-kpis", "children"),
    Output("svc-chart", "figure"),
    Output("svc-table", "children"),
    Input("svc-refresh", "data"),
)
def load_services(_refresh):
    from app.database import get_session, Service, Client

    with get_session() as session:
        services = session.query(Service).all()
        clients = {c.id: c.name for c in session.query(Client).all()}
        data = []
        for s in services:
            data.append({
                "id": s.id,
                "name": s.name,
                "type": s.type,
                "type_label": TYPE_LABELS.get(s.type, s.type),
                "client": clients.get(s.client_id, "—"),
                "value": s.value or 0,
                "cycle": "Mensal" if s.billing_cycle == "monthly" else "Anual",
                "due_date": s.due_date.isoformat() if s.due_date else "",
            })

    today = date.today()
    exp_7 = sum(1 for d in data if d["due_date"] and date.fromisoformat(d["due_date"]) <= today + timedelta(days=7) and date.fromisoformat(d["due_date"]) >= today)
    exp_30 = sum(1 for d in data if d["due_date"] and date.fromisoformat(d["due_date"]) <= today + timedelta(days=30) and date.fromisoformat(d["due_date"]) >= today)

    monthly_total = sum(
        d["value"] if d["cycle"] == "Mensal" else d["value"] / 12
        for d in data
    )
    annual_total = sum(
        d["value"] * 12 if d["cycle"] == "Mensal" else d["value"]
        for d in data
    )

    kpis = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Vencendo em 7 dias", className="kpi-label"),
            html.H3(str(exp_7), className="kpi-value text-danger" if exp_7 > 0 else "kpi-value"),
        ]), className="kpi-card"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Vencendo em 30 dias", className="kpi-label"),
            html.H3(str(exp_30), className="kpi-value text-warning" if exp_30 > 0 else "kpi-value"),
        ]), className="kpi-card"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Custo Mensal", className="kpi-label"),
            html.H3(f"R$ {monthly_total:,.2f}", className="kpi-value"),
        ]), className="kpi-card"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Custo Anual", className="kpi-label"),
            html.H3(f"R$ {annual_total:,.2f}", className="kpi-value"),
        ]), className="kpi-card"), md=3),
    ])

    # Pie chart by type
    type_costs = {}
    for d in data:
        monthly = d["value"] if d["cycle"] == "Mensal" else d["value"] / 12
        type_costs[d["type_label"]] = type_costs.get(d["type_label"], 0) + monthly

    fig = go.Figure(go.Pie(
        labels=list(type_costs.keys()) or ["Sem dados"],
        values=list(type_costs.values()) or [1],
        hole=0.4,
        textinfo="label+percent",
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=30, l=20, r=20),
        title="Custos por Tipo",
        showlegend=False,
        height=300,
    )

    # Table
    col_defs = [
        {"field": "name", "headerName": "Nome", "flex": 2},
        {"field": "type_label", "headerName": "Tipo", "flex": 1},
        {"field": "client", "headerName": "Cliente", "flex": 1},
        {"field": "value", "headerName": "Valor (R$)", "flex": 1,
         "valueFormatter": {"function": "d3.format(',.2f')(params.value)"}},
        {"field": "cycle", "headerName": "Ciclo", "flex": 1},
        {"field": "due_date", "headerName": "Vencimento", "flex": 1},
    ]

    grid = dag.AgGrid(
        id="svc-grid",
        rowData=data,
        columnDefs=col_defs,
        defaultColDef={"sortable": True, "filter": True, "resizable": True},
        className="ag-theme-alpine-dark",
        style={"height": "400px"},
        dashGridOptions={"rowSelection": "single"},
    )

    actions = dbc.Row([
        dbc.Col([
            dbc.Button([html.I(className="bi bi-pencil me-1"), "Editar"], id="svc-edit-btn",
                       size="sm", color="secondary", className="me-2"),
            dbc.Button([html.I(className="bi bi-trash me-1"), "Excluir"], id="svc-del-btn",
                       size="sm", color="danger"),
        ], className="mb-2"),
    ])

    return kpis, fig, html.Div([actions, grid])


# ---------------------------------------------------------------------------
# Client dropdown options helper
# ---------------------------------------------------------------------------

def _client_options():
    from app.database import get_session, Client
    with get_session() as session:
        clients = session.query(Client).filter_by(status="active").order_by(Client.name).all()
        return [{"label": c.name, "value": c.id} for c in clients]


# ---------------------------------------------------------------------------
# Add modal
# ---------------------------------------------------------------------------

@callback(
    Output("svc-add-modal", "is_open"),
    Output("svc-add-name", "value"),
    Output("svc-add-type", "value"),
    Output("svc-add-client", "options"),
    Output("svc-add-client", "value"),
    Output("svc-add-value", "value"),
    Output("svc-add-cycle", "value"),
    Output("svc-add-due", "value"),
    Output("svc-add-notes", "value"),
    Input("svc-open-add", "n_clicks"),
    Input("svc-add-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_add(_open, _cancel):
    if ctx.triggered_id == "svc-open-add":
        return True, "", None, _client_options(), None, None, "monthly", "", ""
    return False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update


@callback(
    Output("svc-add-alert", "children"),
    Output("svc-add-alert", "is_open"),
    Output("svc-add-modal", "is_open", allow_duplicate=True),
    Output("svc-refresh", "data", allow_duplicate=True),
    Output("svc-toast", "children", allow_duplicate=True),
    Output("svc-toast", "header", allow_duplicate=True),
    Output("svc-toast", "is_open", allow_duplicate=True),
    Input("svc-add-save", "n_clicks"),
    State("svc-add-name", "value"),
    State("svc-add-type", "value"),
    State("svc-add-client", "value"),
    State("svc-add-value", "value"),
    State("svc-add-cycle", "value"),
    State("svc-add-due", "value"),
    State("svc-add-notes", "value"),
    State("svc-refresh", "data"),
    prevent_initial_call=True,
)
def save_add(_n, name, stype, client_id, value, cycle, due, notes, refresh):
    if not name or not name.strip():
        return "Nome é obrigatório.", True, no_update, no_update, no_update, no_update, no_update
    if not stype:
        return "Tipo é obrigatório.", True, no_update, no_update, no_update, no_update, no_update

    from app.database import get_session, Service

    try:
        with get_session() as session:
            session.add(Service(
                name=name.strip(),
                type=stype,
                client_id=client_id,
                value=float(value) if value else 0,
                billing_cycle=cycle or "monthly",
                due_date=date.fromisoformat(due) if due else None,
                notes=notes or None,
            ))
        return no_update, False, False, (refresh or 0) + 1, "Serviço criado!", "Serviços", True
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update, no_update, no_update, no_update


# ---------------------------------------------------------------------------
# Edit modal
# ---------------------------------------------------------------------------

@callback(
    Output("svc-edit-modal", "is_open"),
    Output("svc-edit-id", "data"),
    Output("svc-edit-name", "value"),
    Output("svc-edit-type", "value"),
    Output("svc-edit-client", "options"),
    Output("svc-edit-client", "value"),
    Output("svc-edit-value", "value"),
    Output("svc-edit-cycle", "value"),
    Output("svc-edit-due", "value"),
    Output("svc-edit-notes", "value"),
    Input("svc-edit-btn", "n_clicks"),
    Input("svc-edit-cancel", "n_clicks"),
    State("svc-grid", "selectedRows"),
    prevent_initial_call=True,
)
def toggle_edit(_edit, _cancel, selected):
    if ctx.triggered_id == "svc-edit-cancel":
        return False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    if not selected:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

    from app.database import get_session, Service
    sid = selected[0]["id"]

    with get_session() as session:
        s = session.get(Service, sid)
        if not s:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        return (True, sid, s.name, s.type, _client_options(), s.client_id,
                s.value, s.billing_cycle, s.due_date.isoformat() if s.due_date else "", s.notes or "")


@callback(
    Output("svc-edit-alert", "children"),
    Output("svc-edit-alert", "is_open"),
    Output("svc-edit-modal", "is_open", allow_duplicate=True),
    Output("svc-refresh", "data", allow_duplicate=True),
    Output("svc-toast", "children", allow_duplicate=True),
    Output("svc-toast", "header", allow_duplicate=True),
    Output("svc-toast", "is_open", allow_duplicate=True),
    Input("svc-edit-save", "n_clicks"),
    State("svc-edit-id", "data"),
    State("svc-edit-name", "value"),
    State("svc-edit-type", "value"),
    State("svc-edit-client", "value"),
    State("svc-edit-value", "value"),
    State("svc-edit-cycle", "value"),
    State("svc-edit-due", "value"),
    State("svc-edit-notes", "value"),
    State("svc-refresh", "data"),
    prevent_initial_call=True,
)
def save_edit(_n, sid, name, stype, client_id, value, cycle, due, notes, refresh):
    if not name or not name.strip():
        return "Nome é obrigatório.", True, no_update, no_update, no_update, no_update, no_update
    if not stype:
        return "Tipo é obrigatório.", True, no_update, no_update, no_update, no_update, no_update

    from app.database import get_session, Service

    try:
        with get_session() as session:
            s = session.get(Service, sid)
            if not s:
                return "Serviço não encontrado.", True, no_update, no_update, no_update, no_update, no_update
            s.name = name.strip()
            s.type = stype
            s.client_id = client_id
            s.value = float(value) if value else 0
            s.billing_cycle = cycle or "monthly"
            s.due_date = date.fromisoformat(due) if due else None
            s.notes = notes or None
        return no_update, False, False, (refresh or 0) + 1, "Serviço atualizado!", "Serviços", True
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update, no_update, no_update, no_update


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@callback(
    Output("svc-del-modal", "is_open"),
    Output("svc-del-id", "data"),
    Input("svc-del-btn", "n_clicks"),
    Input("svc-del-cancel", "n_clicks"),
    State("svc-grid", "selectedRows"),
    prevent_initial_call=True,
)
def toggle_delete(_del, _cancel, selected):
    if ctx.triggered_id == "svc-del-cancel":
        return False, no_update
    if not selected:
        return no_update, no_update
    return True, selected[0]["id"]


@callback(
    Output("svc-del-modal", "is_open", allow_duplicate=True),
    Output("svc-refresh", "data", allow_duplicate=True),
    Output("svc-toast", "children", allow_duplicate=True),
    Output("svc-toast", "header", allow_duplicate=True),
    Output("svc-toast", "is_open", allow_duplicate=True),
    Input("svc-del-confirm", "n_clicks"),
    State("svc-del-id", "data"),
    State("svc-refresh", "data"),
    prevent_initial_call=True,
)
def confirm_delete(_n, sid, refresh):
    if not sid:
        return False, no_update, no_update, no_update, no_update

    from app.database import get_session, Service

    with get_session() as session:
        s = session.get(Service, sid)
        if s:
            session.delete(s)
    return False, (refresh or 0) + 1, "Serviço excluído.", "Serviços", True
