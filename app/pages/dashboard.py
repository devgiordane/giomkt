"""Dashboard page – KPI cards and spend chart."""

from datetime import date, timedelta

import dash
from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

dash.register_page(__name__, path="/", name="Dashboard")

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = dbc.Container(
    [
        html.H2("Dashboard", className="mb-4 mt-2"),

        # KPI row
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(id="kpi-total-clients", className="kpi-value text-primary"),
                                html.Div("Total de Clientes", className="kpi-label"),
                            ]
                        ),
                        className="kpi-card mb-3",
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(id="kpi-spend-today", className="kpi-value text-success"),
                                html.Div("Gasto Hoje (R$)", className="kpi-label"),
                            ]
                        ),
                        className="kpi-card mb-3",
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(id="kpi-active-campaigns", className="kpi-value text-warning"),
                                html.Div("Campanhas Ativas", className="kpi-label"),
                            ]
                        ),
                        className="kpi-card mb-3",
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(id="kpi-pending-tasks", className="kpi-value text-danger"),
                                html.Div("Tarefas Pendentes", className="kpi-label"),
                            ]
                        ),
                        className="kpi-card mb-3",
                    ),
                    md=3,
                ),
            ],
            className="mb-2",
        ),

        # Spend chart
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("Gasto – Últimos 7 Dias", className="card-title"),
                            dcc.Graph(id="chart-spend-7d", config={"displayModeBar": False}),
                        ]
                    )
                ),
                md=12,
            )
        ),

        # Auto-refresh interval
        dcc.Interval(id="dashboard-interval", interval=60_000, n_intervals=0),
    ],
    fluid=True,
)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("kpi-total-clients", "children"),
    Output("kpi-spend-today", "children"),
    Output("kpi-active-campaigns", "children"),
    Output("kpi-pending-tasks", "children"),
    Output("chart-spend-7d", "figure"),
    Input("dashboard-interval", "n_intervals"),
)
def update_dashboard(_n):
    from app.database import get_session, Client, AccountDailySnapshot, Task

    today = date.today()
    seven_days_ago = today - timedelta(days=6)

    with get_session() as session:
        total_clients = session.query(Client).count()

        today_snapshots = (
            session.query(AccountDailySnapshot)
            .filter(AccountDailySnapshot.date == today)
            .all()
        )
        spend_today = sum(s.spend for s in today_snapshots)

        # "Active campaigns" = distinct clients with a snapshot today
        active_campaigns = len(today_snapshots)

        pending_tasks = (
            session.query(Task).filter_by(status="pending").count()
        )

        # Last 7 days spend
        snapshots_7d = (
            session.query(AccountDailySnapshot)
            .filter(
                AccountDailySnapshot.date >= seven_days_ago,
                AccountDailySnapshot.date <= today,
            )
            .all()
        )

    # Aggregate per day
    daily: dict[date, float] = {}
    for d in range(7):
        day = seven_days_ago + timedelta(days=d)
        daily[day] = 0.0
    for snap in snapshots_7d:
        daily[snap.date] = daily.get(snap.date, 0.0) + snap.spend

    dates = sorted(daily.keys())
    spends = [daily[d] for d in dates]
    date_labels = [d.strftime("%d/%m") for d in dates]

    fig = go.Figure(
        go.Bar(x=date_labels, y=spends, marker_color="#4e73df", name="Gasto (R$)")
    )
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis_title="Data",
        yaxis_title="Gasto (R$)",
    )

    return (
        str(total_clients),
        f"R$ {spend_today:,.2f}",
        str(active_campaigns),
        str(pending_tasks),
        fig,
    )
