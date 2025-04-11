"""Main dashboard application module."""

import dash
import dash_bootstrap_components as dbc
import logging
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
from data_fetch import get_transactions
from get_categories import get_all_categories_api
from functools import lru_cache
from layouts.navbar import navbar
import os

# Configure logger to only log to file, not console
logger = logging.getLogger("budget_app.dashboard")
# Remove any existing handlers (to avoid duplicate logging)
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
# Add file handler only
file_handler = logging.FileHandler("app_debug.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

# Initialize the Dash app with Bootstrap dark theme
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,  # Using Darkly theme for dark mode
        'https://use.fontawesome.com/releases/v5.15.4/css/all.css'  # FontAwesome for icons
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
    assets_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')  # Set assets folder correctly
)

# Cache data fetching
@lru_cache(maxsize=1)
def get_cached_data(spreadsheet_name):
    df = pd.DataFrame(get_transactions(spreadsheet_name, "transactions"))
    # Filter out excluded transactions
    df = df[df['TYPE'] != 'exclude']
    income_cats, expense_cats, _, _ = get_all_categories_api(spreadsheet_name)
    return df, income_cats, expense_cats

# Define the layout structure using the imported navbar
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,  # Using the imported navbar component
    html.Div(id='page-content', className="container-fluid px-4")  # Added container-fluid and padding
], style={"width": "100%", "overflow-x": "hidden"})  # Prevent horizontal scrolling

# Import routes here - make sure the import is done after app is defined
from routes import render_page_content

# Define the callback to update page content
@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    """
    Route to the appropriate page based on URL pathname.
    
    Args:
        pathname: Current URL path
    
    Returns:
        Component: The page content to display
    """
    logger.debug(f"Navigating to path: {pathname}")
    return render_page_content(pathname)

# Log application startup
logger.info("Dashboard initialized")

if __name__ == '__main__': 
    app.run(debug=True)