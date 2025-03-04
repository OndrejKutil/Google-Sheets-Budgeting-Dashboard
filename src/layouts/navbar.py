"""Navigation bar component for the dashboard application.

Defines the main navigation structure and styling.
"""

import dash_bootstrap_components as dbc

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Overview", href="/", active="exact")),
        dbc.NavItem(dbc.NavLink("Transactions", href="/transactions", active="exact")),
        dbc.NavItem(dbc.NavLink("Accounts", href="/accounts", active="exact")),
        dbc.NavItem(dbc.NavLink("Calculator", href="/calculator", active="exact")),
        dbc.NavItem(dbc.NavLink("Setup", href="/setup", active="exact")),
    ],
    brand="Budget Dashboard",
    color="primary",
    dark=True,
    fluid=True,  # Add this line to make navbar span full width
)
