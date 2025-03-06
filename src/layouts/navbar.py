"""Navigation bar component for the Budget Dashboard."""

import dash_bootstrap_components as dbc

# Define the navigation bar
navbar = dbc.Navbar(
    dbc.Container([
        # Brand/logo
        dbc.NavbarBrand("Budget Dashboard", href="/", className="ms-2"),
        
        # Hamburger menu for mobile
        dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
        
        # Navigation links
        dbc.Collapse(
            dbc.Nav([
                dbc.NavItem(dbc.NavLink("Overview", href="/")),
                dbc.NavItem(dbc.NavLink("Transactions", href="/transactions")),
                dbc.NavItem(dbc.NavLink("Accounts", href="/accounts")),
                dbc.NavItem(dbc.NavLink("Calculator", href="/calculator")),
                dbc.NavItem(dbc.NavLink("Setup", href="/setup")),
            ], className="ms-auto", navbar=True),
            id="navbar-collapse",
            navbar=True,
        ),
    ], fluid=True, className="px-0"),  # Added px-0 to remove padding
    color="dark",
    dark=True,
    className="mb-4 w-100",  # Added w-100 for full width
    expand="lg",  # Ensure responsive behavior
    style={"width": "100%"}  # Additional width styling
)
