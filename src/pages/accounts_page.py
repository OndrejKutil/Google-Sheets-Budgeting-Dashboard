import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output
import plotly.express as px
import pandas as pd
from data_fetch import get_transactions
from styles.common_styles import CARD_STYLE, TABLE_STYLE, BUTTON_STYLE
from styles.theme import CHART_THEME, COLORS, TEXT_STYLES

def get_accounts(spreadsheet_name: str) -> list:
    """Retrieve unique account names from the transactions worksheet.
    
    Args:
        spreadsheet_name (str): Name of the Google Sheets spreadsheet

    Returns:
        list: List of unique account names
    """
    transactions = get_transactions(spreadsheet_name, "transactions")
    
    # Extract unique account names
    unique_accounts = set()
    for transaction in transactions:
        account = transaction.get('ACCOUNT', '').strip()
        if account:  # Only add non-empty account names
            unique_accounts.add(account)
    
    # Return sorted list of accounts for consistent display order
    return sorted(list(unique_accounts))

# Define the layout structure for the accounts page
layout = dbc.Container([
    html.H1("Accounts Overview", className="my-4", style=TEXT_STYLES['h1']),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Account Balances", className="card-title text-center mb-4", style=TEXT_STYLES['h4']),
                    dbc.Spinner(html.Div(id="accounts-table")),
                ])
            ], style=CARD_STYLE)
        ], md=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Account Distribution", className="text-center mb-4", style=TEXT_STYLES['h4']),
                    dbc.Spinner(
                        dcc.Graph(id='accounts-pie-chart', figure={})
                    )
                ])
            ], style=CARD_STYLE)
        ], md=6)
    ]),
    html.Div([
        dbc.Button(
            "Update Overview",
            id="update-accounts-button",
            color="primary",
            className="mt-3",
            style=BUTTON_STYLE
        )
    ], className="text-center")
], fluid=True, className="px-4")

@callback(
    [Output('accounts-table', 'children'),
     Output('accounts-pie-chart', 'figure')],
    Input('update-accounts-button', 'n_clicks'),
    prevent_initial_call=False
)
def update_accounts_view(n_clicks):
    """Update the accounts overview with current balances and distribution.
    
    Calculates account balances by:
    1. Starting with initial balances (TYPE == 'start')
    2. Adding all subsequent transactions
    3. Including excluded transactions for accurate balance
    
    Args:
        n_clicks: Button click counter (not used directly)
        
    Returns:
        tuple: (table_component, pie_chart_figure)
    """
    try:
        SPREADSHEET_NAME = "Budget tracker 2025"
        valid_accounts = get_accounts(SPREADSHEET_NAME)
        df = pd.DataFrame(get_transactions(SPREADSHEET_NAME, "transactions"))
        
        # Convert transaction values to numeric format
        df['VALUE_NUMERIC'] = df['VALUE'].str.replace('Kč', '').str.replace(',', '').astype(float)
        
        # Initialize all accounts with zero balance
        account_balances = {account: 0.0 for account in valid_accounts}
        
        # Apply starting balances first
        start_balances = df[df['TYPE'] == 'start'].groupby('ACCOUNT')['VALUE_NUMERIC'].sum()
        for account, balance in start_balances.items():
            if account in account_balances:
                account_balances[account] = balance
        
        # Add all other transactions to the balances
        transactions = df[df['TYPE'] != 'start'].groupby('ACCOUNT')['VALUE_NUMERIC'].sum()
        for account, amount in transactions.items():
            if account in account_balances:
                account_balances[account] += amount
        
        # Generate the accounts table
        table_rows = []
        total_balance = 0
        
        # Create table rows maintaining original account order
        for account in valid_accounts:
            balance = account_balances[account]
            total_balance += balance
            table_rows.append(
                html.Tr([
                    html.Td(account),
                    html.Td(f"{balance:,.2f} Kč", className="text-end text-light")
                ])
            )
        
        # Add the total row at the bottom
        table_rows.append(
            html.Tr([
                html.Td("Total", className="fw-bold"),
                html.Td(f"{total_balance:,.2f} Kč", 
                       className="text-end fw-bold text-light")
            ])
        )
        
        # Create the final table component
        table = dbc.Table([
            html.Thead(html.Tr([
                html.Th("Account"),
                html.Th("Balance", className="text-end")
            ])),
            html.Tbody(table_rows)
        ], bordered=True, hover=True, style=TABLE_STYLE)
        
        # Generate pie chart for positive balances only
        positive_balances = {k: v for k, v in account_balances.items() if v > 0}
        if positive_balances:
            # Define colors from theme for accounts
            account_colors = [COLORS['primary'], COLORS['success'], COLORS['purple'], COLORS['info']]
            
            fig = px.pie(
                values=list(positive_balances.values()),
                names=list(positive_balances.keys()),
                title='Account Distribution',
                template='plotly_dark',
                color_discrete_sequence=account_colors  # Use theme colors
            )
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                title_x=0.5,
                font=dict(color=COLORS['text']),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    y=-0.2,
                    font=dict(color=COLORS['text'])
                )
            )
        else:
            fig = empty_chart("No account balances to display")
        
        return table, fig
    except Exception as e:
        print(f"Error updating accounts view: {e}")
        return html.Div("Error loading accounts data"), {}

def empty_chart(message="No data available"):
    """Create an empty chart with a centered message.
    
    Args:
        message (str): Message to display in empty chart
        
    Returns:
        dict: Plotly figure data structure
    """
    return {
        'data': [],
        'layout': {
            'annotations': [{
                'text': message,
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 20}
            }],
            'height': 400
        }
    }
