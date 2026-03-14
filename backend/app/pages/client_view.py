"""Client detail view page."""

import dash
from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

dash.register_page(__name__, path="/clients/<id>", name="Cliente")


def layout(id=None, **kwargs):
    if id is None:
        return dbc.Container(html.P("Cliente não encontrado."), fluid=True)

    return dbc.Container(
        [
            dcc.Store(id="cv-client-id-store", data=id),
            dbc.Row(
                [
                    dbc.Col(html.H2(id="cv-client-name", children="Carregando..."), md=8),
                    dbc.Col(
                        dbc.Button(
                            [html.I(className="bi bi-pencil me-2"), "Editar"],
                            id="cv-edit-btn",
                            color="outline-primary",
                            size="sm",
                            className="float-end mt-2",
                            disabled=True,
                        ),
                        md=4,
                    ),
                ],
                className="mb-3 mt-2 align-items-center",
            ),

            # Client info card
            dbc.Card(
                dbc.CardBody(id="cv-client-info"),
                className="mb-4",
            ),

            # Budget config card
            dbc.Card(
                [
                    dbc.CardHeader("Configuração de Orçamento"),
                    dbc.CardBody(id="cv-budget-info"),
                ],
                className="mb-4",
            ),

            # Spend history chart
            dbc.Card(
                [
                    dbc.CardHeader("Histórico de Gastos"),
                    dbc.CardBody(dcc.Graph(id="cv-spend-chart", config={"displayModeBar": False})),
                ],
                className="mb-4",
            ),

            # Tasks
            dbc.Card(
                [
                    dbc.CardHeader("Tarefas"),
                    dbc.CardBody(id="cv-tasks-list"),
                ],
                className="mb-4",
            ),

            # Notes
            dbc.Card(
                [
                    dbc.CardHeader("Notas"),
                    dbc.CardBody(id="cv-notes-list"),
                ],
                className="mb-4",
            ),
        ],
        fluid=True,
    )


@callback(
    Output("cv-client-name", "children"),
    Output("cv-client-info", "children"),
    Output("cv-budget-info", "children"),
    Output("cv-spend-chart", "figure"),
    Output("cv-tasks-list", "children"),
    Output("cv-notes-list", "children"),
    Input("cv-client-id-store", "data"),
)
def load_client_view(client_id):
    if not client_id:
        empty_fig = go.Figure(layout={"template": "plotly_dark"})
        return "—", "Não encontrado", "Não encontrado", empty_fig, [], []

    from app.database import get_session, Client, AccountDailySnapshot, Task, Note, ClientBudgetConfig
    from datetime import date, timedelta

    with get_session() as session:
        client = session.get(Client, int(client_id))
        if not client:
            empty_fig = go.Figure(layout={"template": "plotly_dark"})
            return "Cliente não encontrado", "", "", empty_fig, [], []

        # Basic info
        info_content = dbc.Row(
            [
                dbc.Col([html.Strong("Email: "), html.Span(client.email or "—")], md=4),
                dbc.Col([html.Strong("Telefone: "), html.Span(client.phone or "—")], md=4),
                dbc.Col([html.Strong("Status: "), dbc.Badge(client.status, color="success" if client.status == "active" else "secondary")], md=2),
                dbc.Col([html.Strong("FB Account: "), html.Span(client.fb_ad_account_id or "—")], md=6, className="mt-2"),
            ]
        )

        # Budget
        config = client.budget_config
        if config:
            budget_content = dbc.Row(
                [
                    dbc.Col([html.Strong("Limite Diário: "), html.Span(f"R$ {config.daily_limit:,.2f}")], md=3),
                    dbc.Col([html.Strong("Limite Mensal: "), html.Span(f"R$ {config.monthly_limit:,.2f}")], md=3),
                    dbc.Col([html.Strong("Threshold de Alerta: "), html.Span(f"{config.alert_threshold_pct:.0f}%")], md=3),
                ]
            )
        else:
            budget_content = html.P("Nenhuma configuração de orçamento definida.", className="text-muted")

        # Spend history – last 30 days
        today = date.today()
        thirty_ago = today - timedelta(days=29)
        snapshots = (
            session.query(AccountDailySnapshot)
            .filter(
                AccountDailySnapshot.client_id == client.id,
                AccountDailySnapshot.date >= thirty_ago,
            )
            .order_by(AccountDailySnapshot.date)
            .all()
        )

        dates_list = [s.date.strftime("%d/%m") for s in snapshots]
        spends_list = [s.spend for s in snapshots]

        fig = go.Figure(
            go.Bar(x=dates_list, y=spends_list, marker_color="#4e73df", name="Gasto (R$)")
        )
        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis_title="Data",
            yaxis_title="Gasto (R$)",
        )

        # Tasks
        tasks = session.query(Task).filter_by(client_id=client.id).order_by(Task.created_at.desc()).limit(10).all()
        task_items = [
            dbc.ListGroupItem(
                [
                    dbc.Badge("feita" if t.status == "done" else "pendente",
                              color="success" if t.status == "done" else "warning",
                              className="me-2"),
                    html.Strong(t.title),
                    html.Small(f" — {t.created_at.strftime('%d/%m/%Y')}" if t.created_at else "", className="text-muted ms-2"),
                ]
            )
            for t in tasks
        ] or [dbc.ListGroupItem("Nenhuma tarefa.", className="text-muted")]

        tasks_component = dbc.ListGroup(task_items, flush=True)

        # Notes
        notes = session.query(Note).filter_by(client_id=client.id).order_by(Note.created_at.desc()).limit(10).all()
        note_items = [
            dbc.ListGroupItem(
                [
                    html.P(n.content, className="mb-0"),
                    html.Small(n.created_at.strftime("%d/%m/%Y %H:%M") if n.created_at else "", className="text-muted"),
                ]
            )
            for n in notes
        ] or [dbc.ListGroupItem("Nenhuma nota.", className="text-muted")]

        notes_component = dbc.ListGroup(note_items, flush=True)

        name = client.name

    return name, info_content, budget_content, fig, tasks_component, notes_component
