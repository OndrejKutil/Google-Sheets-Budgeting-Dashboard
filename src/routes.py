"""Routing module for the Budget Dashboard application.

Handles URL mapping to different page components.
"""

from dash import html
import dash_bootstrap_components as dbc
import logging
from pages import (
    overview_page, 
    setup_page, 
    accounts_page, 
    transactions_page, 
    calculator_page
)

# Get logger but ensure it's properly configured to avoid duplicates and console output
logger = logging.getLogger("budget_app.routes")

# Remove all handlers to avoid duplicates
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Prevent propagation to root logger (which outputs to console)
logger.propagate = False

# Add file handler only
file_handler = logging.FileHandler("app_debug.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

# Track visited paths to prevent duplicate logging
_last_path = None

def render_page_content(pathname):
    """Render the appropriate page content based on URL pathname.
    
    Args:
        pathname: Current URL path
        
    Returns:
        Component: The page content to display
    """
    global _last_path
    
    # Only log if this is a new path (prevents duplicates)
    if _last_path != pathname:
        logger.info(f"Rendering page for path: {pathname}")
        _last_path = pathname
    
    # Map paths to page layouts
    if pathname == "/":
        return overview_page.layout
    elif pathname == "/setup":
        return setup_page.layout
    elif pathname == "/accounts":
        return accounts_page.layout
    elif pathname == "/transactions":
        return transactions_page.layout
    elif pathname == "/calculator":
        return calculator_page.layout
    
    # If the path is not recognized, return a 404 message
    return dbc.Container([
        html.H1("404: Page Not Found", className="text-danger"),
        html.Hr(),
        html.P(f"The pathname {pathname} was not recognized..."),
        dbc.Button("Go Home", href="/", color="primary")
    ], className="p-5")
