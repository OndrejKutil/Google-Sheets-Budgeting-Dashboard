"""Main dashboard application module.

Initializes and configures the Dash application, handles routing
and page management.
"""

from dash import Dash, html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import pandas as pd
from data_fetch import get_transactions
from get_categories import get_all_categories_api
from functools import lru_cache
from layouts.navbar import navbar
from pages import main_page, monthly_page, yearly_page, setup_page, accounts_page

# Initialize the app with Bootstrap and callback exception suppression
app = Dash(__name__, 
           external_stylesheets=[dbc.themes.DARKLY],
           suppress_callback_exceptions=True)

# Cache data fetching
@lru_cache(maxsize=1)
def get_cached_data(spreadsheet_name):
    df = pd.DataFrame(get_transactions(spreadsheet_name, "transactions"))
    # Filter out excluded transactions
    df = df[df['TYPE'] != 'exclude']
    income_cats, expense_cats, _, _ = get_all_categories_api(spreadsheet_name)
    return df, income_cats, expense_cats

# Remove the create_main_content function as we'll use main_page.layout instead

# Layout - now using imported navbar
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),  # This is the only URL component we need
    navbar,  # Using imported navbar
    html.Div(id='page-content')
])

@callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname: str) -> html.Div:
    """Route to appropriate page based on URL pathname."""
    if pathname == "/monthly":
        return monthly_page.layout
    elif pathname == "/yearly":
        return yearly_page.layout
    elif pathname == "/setup":
        return setup_page.layout
    elif pathname == "/accounts":
        return accounts_page.layout
    else:
        return main_page.layout

if __name__ == '__main__': 
    app.run(debug=True)