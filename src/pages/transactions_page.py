from dash import html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from data_fetch import get_transactions

def get_transactions_data():
    """Safely fetch and process transactions data."""
    try:
        transactions = get_transactions("Budget tracker 2025", "transactions")
        if not transactions:
            return None
        
        df = pd.DataFrame(transactions)
        
        # Convert VALUE to numeric directly
        df['VALUE'] = df['VALUE'].apply(lambda x: float(x.replace('Kč', '').replace(',', '').strip()))
        
        return df
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return None

# Get the data
df = get_transactions_data()

# Define the layout with error handling
layout = dbc.Container([
    html.H1("Transactions Overview", className="my-4"),
    
    dbc.Row([
        dbc.Col([
            html.Div(
                dash_table.DataTable(
                    id='transactions-table',
                    data=df.to_dict('records') if df is not None else [],
                    columns=[{"name": col, "id": col} for col in (df.columns if df is not None else [])],
                    
                    # Enable features
                    sort_action='native',
                    sort_mode='multi',
                    filter_action='native',
                    filter_options={'case': 'insensitive'},
                    
                    # Table style
                    style_table={
                        'overflowX': 'auto',
                        'height': '700px',
                        'border': '1px solid rgb(60, 60, 60)'  # Subtle border for table
                    },
                    
                    # Cell style
                    style_cell={
                        'textAlign': 'left',
                        'padding': '8px 12px',
                        'backgroundColor': 'rgb(50, 50, 50)',
                        'color': 'rgb(220, 220, 220)',  # Slightly dimmed text
                        'height': 'auto',
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis',
                        'border': '1px solid rgb(60, 60, 60)'  # Subtle borders for cells
                    },
                    
                    # Header style
                    style_header={
                        'backgroundColor': 'rgb(40, 40, 40)',
                        'fontWeight': 'bold',
                        'textAlign': 'center',
                        'border': '1px solid rgb(60, 60, 60)'  # Subtle borders for header
                    },
                    
                    # Filter row style
                    style_filter={
                        'backgroundColor': 'rgb(45, 45, 45)',
                    },
                    
                    # Conditional styles - only for VALUE column
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(53, 53, 53)'
                        },
                        {
                            'if': {
                                'filter_query': '{VALUE} < 0',
                                'column_id': 'VALUE'  # Only apply to VALUE column
                            },
                            'color': '#ff7875'
                        },
                        {
                            'if': {
                                'filter_query': '{VALUE} > 0',
                                'column_id': 'VALUE'  # Only apply to VALUE column
                            },
                            'color': '#95de64'
                        }
                    ],
                    
                    # Value column alignment
                    style_cell_conditional=[
                        {
                            'if': {'column_id': 'VALUE'},
                            'textAlign': 'right'
                        }
                    ],
                    
                    # Additional features
                    page_size=15,
                    page_action='native',
                    
                ) if df is not None else html.Div("No data available"),
                style={'width': '100%', 'padding': '20px 0'}
            )
        ], width=12)
    ], className="g-0")
], fluid=True)
