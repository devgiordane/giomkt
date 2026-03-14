import dash
from dash import html, dcc, callback, Input, Output, State, ALL
import dash_bootstrap_components as dbc
from app.database import get_session, Product, ProductMessageFlow

dash.register_page(__name__, path="/message-flows", name="Fluxos de Mensagens")

def layout():
    with get_session() as session:
        products = session.query(Product).all()
        
    product_options = [
        {"label": f"{p.name} (ID Eduzz: {p.product_id_eduzz})", "value": p.id}
        for p in products
    ]

    status_options = [
        {"label": "Aguardando Pagamento", "value": "waitingPayment"},
        {"label": "Pago", "value": "paid"},
        {"label": "Cancelado", "value": "canceled"},
        {"label": "Em Recuperação", "value": "recovering"},
        {"label": "Reembolsado", "value": "refunded"},
        {"label": "Expirado", "value": "expired"},
    ]

    return dbc.Container([
        html.H2("Fluxos de Mensagens por Produto", className="mt-4 mb-3"),
        html.P("Configure mensagens automáticas de WhatsApp baseadas no status da venda."),
        
        # Add Flow Section
        dbc.Card([
            dbc.CardHeader("Adicionar Novo Fluxo"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Selecione o Produto"),
                        dbc.Select(id="flow-product-select", options=product_options, value=product_options[0]["value"] if product_options else None),
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Status da Venda (Gatilho)"),
                        dbc.Select(id="flow-status-select", options=status_options, value="paid"),
                    ], width=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Mensagem"),
                        dbc.Textarea(
                            id="flow-template-input", 
                            placeholder="Olá {name}, seu produto {product} no valor de {value} ...",
                            style={"height": "100px"}
                        ),
                        dbc.FormText("Variáveis disponíveis: {name}, {product}, {value}, {pix_code}, {billet_url}"),
                    ])
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Checkbox(id="flow-active-checkbox", label="Ativo", value=True),
                    ], width=12)
                ], className="mb-3"),
                
                dbc.Button("Salvar Fluxo", id="save-flow-btn", color="primary"),
                html.Div(id="save-flow-msg", className="mt-2")
            ])
        ], className="mb-4"),

        # List Flows Section
        dbc.Card([
            dbc.CardHeader("Fluxos Configurados"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Filtrar por Produto"),
                        dbc.Select(id="filter-product-select", options=[{"label": "Todos", "value": "all"}] + product_options, value="all"),
                    ], width=6)
                ], className="mb-3"),
                
                html.Div(id="flows-list-container")
            ])
        ])
    ], fluid=True)

@callback(
    Output("save-flow-msg", "children"),
    Output("flows-list-container", "children", allow_duplicate=True),
    Input("save-flow-btn", "n_clicks"),
    State("flow-product-select", "value"),
    State("flow-status-select", "value"),
    State("flow-template-input", "value"),
    State("flow-active-checkbox", "value"),
    State("filter-product-select", "value"),
    prevent_initial_call=True
)
def save_flow(n_clicks, product_id, status, template, active, filter_product_id):
    if not n_clicks:
        return "", dash.no_update
        
    if not product_id:
        return dbc.Alert("Selecione um produto.", color="danger"), dash.no_update
        
    if not template or not template.strip():
        return dbc.Alert("A mensagem não pode estar vazia.", color="danger"), dash.no_update

    with get_session() as session:
        new_flow = ProductMessageFlow(
            product_id=int(product_id),
            status=status,
            template=template,
            active=active,
            delay_minutes=0
        )
        session.add(new_flow)
        session.commit()
        
    msg = dbc.Alert("Fluxo salvo com sucesso!", color="success", duration=3000)
    return msg, generate_flows_list(filter_product_id)

@callback(
    Output("flows-list-container", "children"),
    Input("filter-product-select", "value")
)
def update_flows_list(product_id):
    return generate_flows_list(product_id)

@callback(
    Output("flows-list-container", "children", allow_duplicate=True),
    Input({"type": "delete-flow-btn", "index": ALL}, "n_clicks"),
    State("filter-product-select", "value"),
    prevent_initial_call=True
)
def delete_flow(n_clicks_list, filter_product_id):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
        
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    import json
    flow_id = json.loads(button_id)["index"]
    
    with get_session() as session:
        flow = session.query(ProductMessageFlow).get(flow_id)
        if flow:
            session.delete(flow)
            session.commit()
            
    return generate_flows_list(filter_product_id)

@callback(
    Output("flows-list-container", "children", allow_duplicate=True),
    Input({"type": "toggle-flow-btn", "index": ALL}, "n_clicks"),
    State("filter-product-select", "value"),
    prevent_initial_call=True
)
def toggle_flow(n_clicks_list, filter_product_id):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
        
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    import json
    flow_id = json.loads(button_id)["index"]
    
    with get_session() as session:
        flow = session.query(ProductMessageFlow).get(flow_id)
        if flow:
            flow.active = not flow.active
            session.commit()
            
    return generate_flows_list(filter_product_id)


def generate_flows_list(product_id):
    with get_session() as session:
        query = session.query(ProductMessageFlow)
        if product_id and product_id != "all":
            query = query.filter_by(product_id=int(product_id))
        
        flows = query.all()
        
        if not flows:
            return dbc.Alert("Nenhum fluxo encontrado.", color="info")
            
        cards = []
        for flow in flows:
            product_name = flow.product.name if flow.product else "Desconhecido"
            badge_color = "success" if flow.active else "secondary"
            badge_text = "Ativo" if flow.active else "Inativo"
            
            card = dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H5(f"Produto: {product_name}"),
                            html.H6(f"Status Gatilho: {flow.status}", className="text-muted"),
                        ], width=8),
                        dbc.Col([
                            dbc.Badge(badge_text, color=badge_color, className="float-end fs-6")
                        ], width=4)
                    ]),
                    html.Hr(),
                    html.P(flow.template, style={"whiteSpace": "pre-wrap"}),
                    html.Div([
                        dbc.Button(
                            "Alternar Status", 
                            id={"type": "toggle-flow-btn", "index": flow.id}, 
                            color="warning", 
                            size="sm", 
                            className="me-2"
                        ),
                        dbc.Button(
                            "Excluir", 
                            id={"type": "delete-flow-btn", "index": flow.id}, 
                            color="danger", 
                            size="sm"
                        )
                    ], className="mt-3")
                ])
            ], className="mb-3")
            cards.append(card)
            
        return html.Div(cards)
