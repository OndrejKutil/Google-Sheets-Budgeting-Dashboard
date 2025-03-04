from dash import html, dash_table, callback, Input, Output
import dash_bootstrap_components as dbc
import math
from data_fetch import get_transactions

def get_transactions_data():
    """Fetch raw transactions data."""
    try:
        transactions = get_transactions("Budget tracker 2025", "transactions")
        if transactions:
            columns = list(transactions[0].keys())
            # Calculate last page number (page_size is 25)
            last_page = math.ceil(len(transactions) / 25) - 1
            return transactions, columns, last_page
        return [], [], 0
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return [], [], 0

# Get initial data
data, columns, last_page = get_transactions_data()

layout = dbc.Container([
    html.H1("Transactions", className="my-4"),
    
    dash_table.DataTable(
        id='transactions-table',
        data=data,
        columns=[{"name": col, "id": col} for col in columns],
        
        # Core functionality
        sort_action='native',
        sort_mode='multi',
        filter_action='native',
        filter_options={'case': 'insensitive'},
        page_action='native',
        page_size=25,
        page_current=last_page,  # Start at the last page
        
        # Features
        row_selectable=False,
        cell_selectable=True,
        tooltip_delay=0,
        tooltip_duration=None,
        
        # Styling
        style_table={
            'overflowX': 'auto',
            'overflowY': 'auto',
            'minWidth': '100%',
        },
        style_cell={
            'textAlign': 'left',
            'padding': '12px 15px',
            'backgroundColor': 'rgb(50, 50, 50)',
            'color': 'white',
            'fontSize': '14px',
            'fontFamily': 'system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, "Helvetica Neue", sans-serif',
            'minWidth': '100px',
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        style_header={
            'backgroundColor': 'rgb(35, 35, 35)',
            'fontWeight': '600',
            'textTransform': 'uppercase',
            'fontSize': '12px',
            'letterSpacing': '0.5px',
            'borderBottom': '2px solid rgb(80, 80, 80)',
        },
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto',
            'lineHeight': '20px',
        },
        style_filter={
            'backgroundColor': 'rgb(45, 45, 45)',
            'padding': '8px',
        },
        
        # Conditional styling
        style_data_conditional=[
            {
                'if': {'state': 'selected'},
                'backgroundColor': 'rgba(0, 116, 217, 0.3)',
                'border': '1px solid rgb(0, 116, 217)',
            },
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(55, 55, 55)',
            },
            {
                'if': {'filter_query': '{VALUE} contains "-"'},
                'color': '#ff7875'  # Red for negative values
            },
            {
                'if': {'filter_query': '{VALUE} > 0'},
                'color': '#95de64'  # Green for positive values
            }
        ],
        
        # Tooltip styling
        css=[{
            'selector': '.dash-table-tooltip',
            'rule': 'background-color: rgb(50, 50, 50) !important; color: white !important;'
        }]
    )
], fluid=True, className="mb-5")

# Add callback to refresh data
@callback(
    [Output('transactions-table', 'data'),
     Output('transactions-table', 'columns'),
     Output('transactions-table', 'page_current')],
    [Input('url', 'pathname')]
)
def refresh_data(_):
    """Refresh data when navigating to the page."""
    data, columns, last_page = get_transactions_data()
    return (
        data,
        [{"name": col, "id": col} for col in columns],
        last_page
    )
