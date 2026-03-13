import dash
from dash import html
import dash_bootstrap_components as dbc


def create_sidebar():
    nav_items = [
        {"label": "Dashboard", "href": "/", "icon": "bi bi-speedometer2"},
        {"label": "Clientes", "href": "/clients", "icon": "bi bi-people"},
        {"label": "Campanhas", "href": "/campaigns", "icon": "bi bi-megaphone"},
        {"label": "Hoje", "href": "/today", "icon": "bi bi-sun"},
        {"label": "Tarefas", "href": "/tasks", "icon": "bi bi-check2-square"},
        {"label": "Em breve", "href": "/upcoming", "icon": "bi bi-calendar-week"},
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
        ],
        id="sidebar",
    )
    return sidebar


def create_layout():
    sidebar = create_sidebar()
    content = html.Div(
        dash.page_container,
        id="page-content",
    )
    return dbc.Container(
        [sidebar, content],
        fluid=True,
        className="p-0",
    )
