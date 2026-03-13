"""Umami Analytics dashboard page."""

import time
from datetime import date, timedelta

import dash
from dash import html, dcc, callback, Output, Input, State, no_update, ctx
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import plotly.graph_objects as go

dash.register_page(__name__, path="/analytics", name="Analytics")

PERIOD_OPTIONS = [
    {"label": "7 dias", "value": 7},
    {"label": "30 dias", "value": 30},
    {"label": "90 dias", "value": 90},
]

layout = dbc.Container([
    dcc.Store(id="ana-refresh", data=0),
    dcc.Store(id="ana-edit-id"),
    dcc.Store(id="ana-del-id"),

    # Add site modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Novo Site")),
        dbc.ModalBody([
            dbc.Alert(id="ana-add-alert", is_open=False, color="danger"),
            dbc.Row([
                dbc.Col([dbc.Label("Nome *"), dbc.Input(id="ana-add-name")], md=6, className="mb-3"),
                dbc.Col([dbc.Label("Domínio *"), dbc.Input(id="ana-add-domain", placeholder="exemplo.com.br")], md=6, className="mb-3"),
            ]),
            dbc.Row([
                dbc.Col([dbc.Label("Umami Site ID"), dbc.Input(id="ana-add-umami-id", placeholder="UUID do Umami")], md=6, className="mb-3"),
                dbc.Col([dbc.Label("Cliente"), dcc.Dropdown(id="ana-add-client")], md=6, className="mb-3"),
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="ana-add-cancel", color="secondary", className="me-2"),
            dbc.Button("Salvar", id="ana-add-save", color="primary"),
        ]),
    ], id="ana-add-modal", is_open=False),

    # Delete confirm
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Confirmar exclusão")),
        dbc.ModalBody("Excluir este site?"),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="ana-del-cancel", color="secondary", className="me-2"),
            dbc.Button("Excluir", id="ana-del-confirm", color="danger"),
        ]),
    ], id="ana-del-modal", is_open=False),

    # Header
    dbc.Row([
        dbc.Col(html.H2([html.I(className="bi bi-bar-chart-line me-2"), "Analytics"]), md=6),
        dbc.Col(
            dbc.Button([html.I(className="bi bi-plus-circle me-2"), "Novo Site"],
                       id="ana-open-add", color="primary"),
            md=6, className="text-end",
        ),
    ], className="mb-4 mt-2 align-items-center"),

    # Site selector + period
    dbc.Row([
        dbc.Col([dbc.Label("Site:"), dcc.Dropdown(id="ana-site-select")], md=4, className="mb-3"),
        dbc.Col([dbc.Label("Período:"), dcc.Dropdown(id="ana-period", options=PERIOD_OPTIONS, value=30, clearable=False)], md=2, className="mb-3"),
        dbc.Col([
            dbc.Label("\u00a0"),
            html.Div(dbc.Button([html.I(className="bi bi-arrow-repeat me-1"), "Atualizar"], id="ana-fetch-btn", color="info")),
        ], md=2, className="mb-3"),
    ]),

    # KPIs
    html.Div(id="ana-kpis", className="mb-4"),

    # Charts
    dbc.Row([
        dbc.Col(dcc.Graph(id="ana-pageviews-chart", config={"displayModeBar": False}), md=7),
        dbc.Col(dcc.Graph(id="ana-top-pages-chart", config={"displayModeBar": False}), md=5),
    ], className="mb-4"),

    # Sites management
    html.Hr(),
    html.H5("Sites cadastrados", className="mb-3"),
    html.Div(id="ana-sites-table"),

    dbc.Toast(id="ana-toast", header="Analytics", is_open=False, dismissable=True, duration=3000,
              style={"position": "fixed", "bottom": "1rem", "right": "1rem", "zIndex": 9999}),
], fluid=True)


def _client_options():
    from app.database import get_session, Client
    with get_session() as session:
        return [{"label": c.name, "value": c.id}
                for c in session.query(Client).filter_by(status="active").order_by(Client.name).all()]


def _site_options():
    from app.database import get_session, Site
    with get_session() as session:
        return [{"label": s.name, "value": s.id}
                for s in session.query(Site).order_by(Site.name).all()]


# Load sites list
@callback(
    Output("ana-sites-table", "children"),
    Output("ana-site-select", "options"),
    Input("ana-refresh", "data"),
)
def load_sites(_refresh):
    from app.database import get_session, Site, Client

    with get_session() as session:
        sites = session.query(Site).order_by(Site.name).all()
        clients = {c.id: c.name for c in session.query(Client).all()}
        data = [{"id": s.id, "name": s.name, "domain": s.domain,
                 "umami_id": s.umami_site_id or "", "client": clients.get(s.client_id, "—")}
                for s in sites]

    opts = [{"label": d["name"], "value": d["id"]} for d in data]

    if not data:
        return dbc.Alert("Nenhum site cadastrado.", color="info"), opts

    col_defs = [
        {"field": "name", "headerName": "Nome", "flex": 1.5},
        {"field": "domain", "headerName": "Domínio", "flex": 2},
        {"field": "umami_id", "headerName": "Umami ID", "flex": 1.5},
        {"field": "client", "headerName": "Cliente", "flex": 1},
    ]

    actions = dbc.Row([dbc.Col([
        dbc.Button([html.I(className="bi bi-trash me-1"), "Excluir"], id="ana-del-btn", size="sm", color="danger"),
    ], className="mb-2")])

    grid = dag.AgGrid(
        id="ana-grid", rowData=data, columnDefs=col_defs,
        defaultColDef={"sortable": True, "resizable": True},
        className="ag-theme-alpine-dark", style={"height": "250px"},
        dashGridOptions={"rowSelection": "single"},
    )

    return html.Div([actions, grid]), opts


# Fetch analytics
@callback(
    Output("ana-kpis", "children"),
    Output("ana-pageviews-chart", "figure"),
    Output("ana-top-pages-chart", "figure"),
    Input("ana-fetch-btn", "n_clicks"),
    State("ana-site-select", "value"),
    State("ana-period", "value"),
    prevent_initial_call=True,
)
def fetch_analytics(_n, site_id, days):
    from app.config import UMAMI_API_URL, UMAMI_API_TOKEN

    if not UMAMI_API_URL or not UMAMI_API_TOKEN:
        empty = go.Figure().update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return dbc.Alert("Configure UMAMI_API_URL e UMAMI_API_TOKEN no .env", color="warning"), empty, empty

    if not site_id:
        empty = go.Figure().update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return dbc.Alert("Selecione um site.", color="info"), empty, empty

    from app.database import get_session, Site
    with get_session() as session:
        site = session.get(Site, site_id)
        if not site or not site.umami_site_id:
            empty = go.Figure().update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            return dbc.Alert("Site sem Umami ID configurado.", color="warning"), empty, empty
        umami_id = site.umami_site_id

    from app.services.umami import get_website_stats, get_website_pageviews, get_website_metrics

    end_at = int(time.time() * 1000)
    start_at = int((time.time() - days * 86400) * 1000)

    stats = get_website_stats(umami_id, start_at, end_at)
    pageviews = get_website_pageviews(umami_id, start_at, end_at, "day")
    top_pages = get_website_metrics(umami_id, start_at, end_at, "url")

    # KPIs
    pv = stats.get("pageviews", {}).get("value", 0) if stats else 0
    visitors = stats.get("visitors", {}).get("value", 0) if stats else 0
    bounces = stats.get("bounces", {}).get("value", 0) if stats else 0
    totaltime = stats.get("totaltime", {}).get("value", 0) if stats else 0
    avg_time = totaltime / visitors if visitors else 0
    bounce_rate = (bounces / visitors * 100) if visitors else 0

    kpis = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Pageviews", className="kpi-label"),
            html.H3(f"{pv:,}", className="kpi-value"),
        ]), className="kpi-card"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Visitantes", className="kpi-label"),
            html.H3(f"{visitors:,}", className="kpi-value"),
        ]), className="kpi-card"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Bounce Rate", className="kpi-label"),
            html.H3(f"{bounce_rate:.1f}%", className="kpi-value"),
        ]), className="kpi-card"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Tempo Médio", className="kpi-label"),
            html.H3(f"{avg_time:.0f}s", className="kpi-value"),
        ]), className="kpi-card"), md=3),
    ])

    # Pageviews chart
    fig_pv = go.Figure()
    if pageviews and "pageviews" in pageviews:
        dates = [p.get("x", "") for p in pageviews["pageviews"]]
        values = [p.get("y", 0) for p in pageviews["pageviews"]]
        fig_pv.add_trace(go.Scatter(x=dates, y=values, mode="lines+markers", name="Pageviews", line=dict(color="#0d6efd")))
    fig_pv.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title="Pageviews por Dia", margin=dict(t=40, b=40, l=40, r=20), height=300,
    )

    # Top pages chart
    fig_tp = go.Figure()
    if top_pages:
        pages = top_pages[:10]
        names = [p.get("x", "?") for p in pages]
        counts = [p.get("y", 0) for p in pages]
        fig_tp.add_trace(go.Bar(y=names, x=counts, orientation="h", marker_color="#198754"))
    fig_tp.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title="Top Páginas", margin=dict(t=40, b=40, l=120, r=20), height=300,
        yaxis=dict(autorange="reversed"),
    )

    return kpis, fig_pv, fig_tp


# Add site
@callback(
    Output("ana-add-modal", "is_open"),
    Output("ana-add-name", "value"), Output("ana-add-domain", "value"),
    Output("ana-add-umami-id", "value"), Output("ana-add-client", "options"), Output("ana-add-client", "value"),
    Input("ana-open-add", "n_clicks"), Input("ana-add-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_add(_o, _c):
    if ctx.triggered_id == "ana-open-add":
        return True, "", "", "", _client_options(), None
    return False, no_update, no_update, no_update, no_update, no_update


@callback(
    Output("ana-add-alert", "children"), Output("ana-add-alert", "is_open"),
    Output("ana-add-modal", "is_open", allow_duplicate=True),
    Output("ana-refresh", "data", allow_duplicate=True),
    Output("ana-toast", "children", allow_duplicate=True), Output("ana-toast", "is_open", allow_duplicate=True),
    Input("ana-add-save", "n_clicks"),
    State("ana-add-name", "value"), State("ana-add-domain", "value"),
    State("ana-add-umami-id", "value"), State("ana-add-client", "value"),
    State("ana-refresh", "data"),
    prevent_initial_call=True,
)
def save_add(_n, name, domain, umami_id, client_id, refresh):
    if not name or not name.strip():
        return "Nome é obrigatório.", True, no_update, no_update, no_update, no_update
    if not domain or not domain.strip():
        return "Domínio é obrigatório.", True, no_update, no_update, no_update, no_update

    from app.database import get_session, Site
    try:
        with get_session() as session:
            session.add(Site(
                name=name.strip(), domain=domain.strip(),
                umami_site_id=umami_id or None, client_id=client_id,
            ))
        return no_update, False, False, (refresh or 0) + 1, "Site cadastrado!", True
    except Exception as exc:
        return f"Erro: {exc}", True, no_update, no_update, no_update, no_update


# Delete site
@callback(
    Output("ana-del-modal", "is_open"), Output("ana-del-id", "data"),
    Input("ana-del-btn", "n_clicks"), Input("ana-del-cancel", "n_clicks"),
    State("ana-grid", "selectedRows"),
    prevent_initial_call=True,
)
def toggle_delete(_d, _c, selected):
    if ctx.triggered_id == "ana-del-cancel" or not selected:
        return False, no_update
    return True, selected[0]["id"]


@callback(
    Output("ana-del-modal", "is_open", allow_duplicate=True),
    Output("ana-refresh", "data", allow_duplicate=True),
    Output("ana-toast", "children", allow_duplicate=True), Output("ana-toast", "is_open", allow_duplicate=True),
    Input("ana-del-confirm", "n_clicks"),
    State("ana-del-id", "data"), State("ana-refresh", "data"),
    prevent_initial_call=True,
)
def confirm_delete(_n, sid, refresh):
    if not sid:
        return False, no_update, no_update, no_update
    from app.database import get_session, Site
    with get_session() as session:
        s = session.get(Site, sid)
        if s:
            session.delete(s)
    return False, (refresh or 0) + 1, "Site excluído.", True
