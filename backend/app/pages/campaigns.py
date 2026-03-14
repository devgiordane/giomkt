"""Campaigns page – spend cards and snapshot table."""

from datetime import date

import dash
from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import plotly.express as px

dash.register_page(__name__, path="/campaigns", name="Campanhas")

layout = dbc.Container(
    [
        html.H2("Campanhas", className="mb-4 mt-2"),
        dbc.Row(id="campaigns-spend-cards", className="mb-4"),
        dbc.Row(
            dbc.Col(
                dag.AgGrid(
                    id="campaigns-grid",
                    columnDefs=[
                        {"field": "client", "headerName": "Cliente", "flex": 2},
                        {"field": "date", "headerName": "Data", "width": 120},
                        {"field": "spend", "headerName": "Gasto (R$)", "width": 140, "valueFormatter": {"function": "params.value.toFixed(2)"}},
                        {"field": "impressions", "headerName": "Impressões", "width": 140},
                        {"field": "clicks", "headerName": "Cliques", "width": 120},
                    ],
                    rowData=[],
                    defaultColDef={"resizable": True, "sortable": True, "filter": True},
                    dashGridOptions={"pagination": True, "paginationPageSize": 25},
                    style={"height": "450px"},
                    className="ag-theme-alpine-dark",
                )
            )
        ),
        dcc.Interval(id="campaigns-interval", interval=60_000, n_intervals=0),
    ],
    fluid=True,
)


@callback(
    Output("campaigns-grid", "rowData"),
    Output("campaigns-spend-cards", "children"),
    Input("campaigns-interval", "n_intervals"),
)
def load_campaigns(_n):
    from app.database import get_session, Client, AccountDailySnapshot

    today = date.today()

    with get_session() as session:
        snapshots = (
            session.query(AccountDailySnapshot)
            .order_by(AccountDailySnapshot.date.desc())
            .limit(200)
            .all()
        )

        client_map = {c.id: c.name for c in session.query(Client).all()}

        rows = [
            {
                "client": client_map.get(s.client_id, f"#{s.client_id}"),
                "date": s.date.strftime("%d/%m/%Y"),
                "spend": s.spend,
                "impressions": s.impressions,
                "clicks": s.clicks,
            }
            for s in snapshots
        ]

        # Today's spend per client card
        today_snaps = [s for s in snapshots if s.date == today]
        cards = []
        for snap in today_snaps:
            client_name = client_map.get(snap.client_id, f"#{snap.client_id}")
            cards.append(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5(client_name, className="card-title text-truncate"),
                                html.H3(f"R$ {snap.spend:,.2f}", className="text-success"),
                                html.Small(f"{snap.impressions:,} impressões · {snap.clicks:,} cliques", className="text-muted"),
                            ]
                        ),
                        className="kpi-card mb-3",
                    ),
                    md=3,
                )
            )

        if not cards:
            cards = [dbc.Col(html.P("Nenhum dado disponível para hoje.", className="text-muted"))]

    return rows, cards
