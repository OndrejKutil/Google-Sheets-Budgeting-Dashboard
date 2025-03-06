from dash import html, dash_table, callback, Input, Output
import dash_bootstrap_components as dbc
import math
from data_fetch import get_transactions
from styles.common_styles import DATATABLE_STYLE
from styles.theme import COLORS, TEXT_STYLES

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
    html.H1("Transactions", className="my-4", style=TEXT_STYLES['h1']),
    
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
        page_current=last_page,
        
        # Features
        row_selectable=False,
        cell_selectable=True,
        tooltip_delay=0,
        tooltip_duration=None,
        
        # Styling
        style_table=DATATABLE_STYLE['table'],
        style_cell=DATATABLE_STYLE['cell'],
        style_header=DATATABLE_STYLE['header'],
        style_filter=DATATABLE_STYLE['filter'],
        
        # Conditional styling
        style_data_conditional=[
            {
                'if': {'state': 'selected'},
                'backgroundColor': f'{COLORS["primary"]}33',
                'border': f'1px solid {COLORS["primary"]}',
            },
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': COLORS['background'],
            },
            {
                'if': {'filter_query': '{VALUE} contains "-"'},
                'color': COLORS['danger']
            },
            {
                'if': {'filter_query': '{VALUE} > 0'},
                'color': COLORS['success']
            }
        ],
        
        # Tooltip styling
        css=[{
            'selector': '.dash-table-tooltip',
            'rule': f'background-color: {COLORS["surface"]} !important; color: {COLORS["text"]} !important;'
        }]
    )
], fluid=True, className="mb-5", style={'backgroundColor': COLORS['background']})

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
