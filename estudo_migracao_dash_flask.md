# Estudo Técnico: Migração de Plotly Dash para API REST Flask

## 1. Análise da Arquitetura Atual do Projeto Dash

O backend atual é um monólito que combina o servidor web Flask (subjacente) com a camada de visualização interativa do Plotly Dash.

**Características atuais:**

- O arquivo `app/main.py` atua como entrypoint, instanciando o Flask e o Dash em conjunto. Já possui algumas rotas REST nativas do Flask implementadas (ex: `/api/health`, webhooks da EvolutionAPI e Eduzz).
- A interface gráfica está espalhada na pasta `app/pages/`, com mais de 20 páginas (ex: `dashboard.py`, `clients.py`, `analytics.py`), utilizando componentes do Dash (`html`, `dcc`, `dbc`).
- Cada página contém tanto a definição visual (`layout`) quanto a reatividade via decorators (`@callback`).
- A lógica de negócios, integrações e consultas estão parcialmente desacopladas em `app/services/` e `app/database.py`, mas frequentemente são importadas e executadas diretamente dentro dos callbacks do Dash.
- O Dash gerencia o estado da sessão e das telas pelo frontend, comunicando-se de forma transparente via AJAX (mas enviando layouts e dados acoplados).

## 2. Identificação da Lógica Reutilizável

O objetivo é manter o máximo de código focado no negócio. Componentes que devem ser mantidos sem alterações (ou com mínimas adaptações):

- **Modelos de Banco de Dados (`app/database.py`):** As tabelas, sessões SQLAlchemy e queries ORM se mantêm exatamente como estão.
- **Serviços (`app/services/*.py`):** Lógicas de integração (Eduzz, Facebook, WhatsApp, Umami), IA e alertas estão encapsulados de forma independente do Dash. Podem ser injetados diretamente nas novas rotas Flask.
- **Consultas e Agregações de Dados:** O processamento numérico, lógica com pandas e queries SQLAlchemy presentes nos callbacks podem ser recortados e reaproveitados para montar as respostas JSON dos endpoints REST.
- **Webhooks Existentes:** Rotas puras de Flask em `main.py` que não interagem com o Dash podem continuar operando normalmente.

## 3. Mapeamento de Callbacks Dash para Endpoints REST

A mudança de paradigma consiste em sair de um modelo reativo orientado a eventos visuais (`Input`/`Output`) para requisições HTTP (`GET`, `POST`, `PUT`, `DELETE`).

**Exemplos de Mapeamento:**

| Como é no Dash                                                    | Como será no Flask (REST)                                  | Método HTTP Sugerido |
| ----------------------------------------------------------------- | ---------------------------------------------------------- | -------------------- |
| Callback que atualiza KPIs do Dashboard                           | `/api/dashboard/kpis`                                      | `GET`                |
| Callback que popula tabela de clientes                            | `/api/clients` (com paginação/filtros via query params)    | `GET`                |
| Callback de submissão do formulário de cliente (`client_form.py`) | `/api/clients`                                             | `POST` / `PUT`       |
| Callback para excluir uma tarefa (`tasks.py`)                     | `/api/tasks/<id>`                                          | `DELETE`             |
| Callback gerando um gráfico Plotly                                | `/api/analytics/spend-chart` (retorna série temporal JSON) | `GET`                |

_Nota:_ O envio de gráficos (`go.Figure`) não deve ocorrer na API. O backend retornará os dados puros (séries, eixos) em JSON, e a renderização do gráfico acontecerá no frontend Next.js usando Recharts, Chart.js ou mesmo Plotly.js.

## 4. Estratégia para Remover Dependências do Dash

1. **Remoção de Bibliotecas:** Remover do `pyproject.toml` pacotes como `dash`, `dash-bootstrap-components` e `plotly` (caso o Plotly não seja necessário para fins não-visuais do servidor).
2. **Exclusão da Camada Visual:** Apagar com segurança os arquivos `app/layout.py` e a pasta `app/assets/`.
3. **Refatoração Inicial (Entrypoint):** Limpar `app/main.py` para instanciar estritamente o `Flask(__name__)`, removendo a declaração de `dash.Dash`.
4. **Substituição de Callbacks:** Para cada página em `app/pages/`:
   - Identificar e copiar as queries de banco de dados e regras de negócio presentes no corpo dos callbacks.
   - Descartar todos os objetos de UI (`dbc.Row`, `html.Div`, `dcc.Graph`).
   - Transferir a lógica de dados para controladores (rotas Flask).
   - Apagar as páginas Dash.

## 5. Proposta de Estrutura de Projeto Flask Organizada

A arquitetura orientada a blueprints é ideal para organizar a API REST.

```text
backend/
├── pyproject.toml
├── app/
│   ├── __init__.py         # Fábrica da aplicação (create_app)
│   ├── config.py           # Configurações do ambiente
│   ├── database.py         # Conexão SQLAlchemy e Models
│   ├── api/                # Rotas organizadas por domínios (Blueprints)
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   ├── clients.py
│   │   ├── campaigns.py
│   │   └── webhooks.py
│   └── services/           # Lógica de negócio reutilizada e intocada
│       ├── ai_assistant.py
│       ├── facebook.py
│       └── whatsapp.py
└── data/
```

## 6. Plano de Migração Passo a Passo

- **Passo 1: Setup do Flask e Estrutura Inicial**
  - Configurar um `create_app()` no `app/__init__.py`.
  - Criar o diretório `api/` para receber os Flask Blueprints.
- **Passo 2: Migração de APIs base (Sem UI Atrelada)**
  - Migrar os webhooks (Eduzz, WhatsApp) existentes em `main.py` para dentro de `app/api/webhooks.py`.
- **Passo 3: Conversão Gradual das Páginas para Blueprints REST**
  - Para cada página do módulo atual (`dashboard`, `clients`, `tasks`, etc.):
    - Criar o respectivo blueprint (ex: `api/dashboard.py`).
    - Traduzir a lógica do callback de extração de dados para um retorno JSON.
    - Excluir o arquivo original em `pages/`.
- **Passo 4: Adequação das Respostas (JSON Serialization)**
  - O Dash converte alguns tipos automaticamente. No REST, será preciso garantir que objetos de data (`datetime`), UUIDs e models do SQLAlchemy sejam serializados corretamente em JSON. (Pode-se usar `marshmallow` ou o próprio `jsonify` customizado).
- **Passo 5: Limpeza Final de Dependências**
  - Remover do código todos os imports do Dash.
  - Atualizar os arquivos de dependência (Poetry/Pip).
  - Executar os testes para garantir a integridade dos `services/`.

## 7. Riscos Comuns Nesse Tipo de Refatoração

1. **Vazamento de Lógica de Negócio na UI:** Em Dash, é comum que a formatação do dado aconteça na mesma função da query de banco. Risco de perder formatações vitais ou enviar dados excessivos pro Next.js.
2. **Serialização de Dados Complexos:** Retornar models do SQLAlchemy direto com `jsonify` resultará em erro. É preciso serializar o objeto para `dict` antes do envio.
3. **Nomenclatura e Paginação:** Callbacks Dash muitas vezes trazem todos os dados para o DataTable. Na API REST será recomendado introduzir paginação para que a rota `/api/clients` não seja um gargalo.
4. **Ausência de Contratos de API:** Ao remover a UI acoplada, o frontend em Next.js exigirá clareza nas estruturas JSON enviadas. Documentar a API (via Swagger/Flasgger/OpenAPI) será crucial durante o desenvolvimento.

## 8. Exemplo de Conversão de Callback Dash para Rota Flask

### Antes (Dash): `app/pages/dashboard.py`

```python
@callback(
    Output("kpi-total-clients", "children"),
    Output("kpi-spend-today", "children"),
    Input("dashboard-interval", "n_intervals"),
)
def update_dashboard(_n):
    from app.database import get_session, Client, AccountDailySnapshot
    from datetime import date
    today = date.today()

    with get_session() as session:
        total_clients = session.query(Client).count()
        today_snapshots = session.query(AccountDailySnapshot).filter_by(date=today).all()
        spend_today = sum(s.spend for s in today_snapshots)

    # Retorna componentes visuais ou textos formatados
    return (str(total_clients), f"R$ {spend_today:,.2f}")
```

### Depois (Flask API REST): `app/api/dashboard.py`

```python
from flask import Blueprint, jsonify
from datetime import date
from app.database import get_session, Client, AccountDailySnapshot

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/api/dashboard/kpis", methods=["GET"])
def get_kpis():
    today = date.today()

    with get_session() as session:
        total_clients = session.query(Client).count()
        today_snapshots = session.query(AccountDailySnapshot).filter_by(date=today).all()
        spend_today = sum(s.spend for s in today_snapshots)
        active_campaigns = len(today_snapshots)

    # Retorna um objeto JSON puro. Formatação (ex: R$) fica a cargo do frontend.
    return jsonify({
        "total_clients": total_clients,
        "spend_today": spend_today,
        "active_campaigns": active_campaigns
    }), 200
```

**Benefícios Imediatos:**

- Separação clara: O Backend provê dados.
- Frontend (Next.js) recebe o JSON e formata como e onde quiser.
- Menor overhead de banda em comparação ao Dash, que empacota callbacks e Virtual DOM no tráfego HTTP.
