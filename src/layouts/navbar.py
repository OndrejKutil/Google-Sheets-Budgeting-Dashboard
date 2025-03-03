"""Navigation bar component for the dashboard application.

Defines the main navigation structure and styling.
"""

import dash_bootstrap_components as dbc

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Main", href="/", active="exact")),
        dbc.NavItem(dbc.NavLink("Monthly Overview", href="/monthly", active="exact")),
        dbc.NavItem(dbc.NavLink("Yearly Overview", href="/yearly", active="exact")),
        dbc.NavItem(dbc.NavLink("Savings", href="/savings", active="exact")),  # Added this line
        dbc.NavItem(dbc.NavLink("Transactions", href="/transactions", active="exact")),
        dbc.NavItem(dbc.NavLink("Accounts", href="/accounts", active="exact")),
        dbc.NavItem(dbc.NavLink("Calculator", href="/calculator", active="exact")),
        dbc.NavItem(dbc.NavLink("Setup", href="/setup", active="exact")),
        
    ],
    brand="Budget Dashboard",
    color="primary",
    dark=True,
)
