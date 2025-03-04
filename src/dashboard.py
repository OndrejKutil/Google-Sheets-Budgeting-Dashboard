"""Main dashboard application module."""

from dash import Dash, html, dcc, Output, Input, State
import dash_bootstrap_components as dbc
import pandas as pd
from data_fetch import get_transactions
from get_categories import get_all_categories_api
from functools import lru_cache
from layouts.navbar import navbar
from pages import overview_page, setup_page, accounts_page, transactions_page, savings_page, calculator_page

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

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content')
])

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname: str) -> html.Div:
    """Route to appropriate page based on URL pathname."""
    if pathname == "/calculator":
        return calculator_page.layout
    elif pathname == "/setup":
        return setup_page.layout
    elif pathname == "/accounts":
        return accounts_page.layout
    elif pathname == "/transactions":
        return transactions_page.layout
    else:
        return overview_page.layout

if __name__ == '__main__': 
    app.run(debug=True)