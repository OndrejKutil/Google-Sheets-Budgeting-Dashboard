from dash import html, dcc, callback, Input, Output, State, ALL, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from investment_calc import calculate_investment_growth
import json

# Styling
THEME = {
    'background': '#2d2d2d',
    'surface': '#1a1a1a',
    'text': '#ffffff',
    'primary': '#3498db',
    'success': '#2ecc71',
    'muted': '#adb5bd'
}

CARD_STYLE = {
    'backgroundColor': THEME['background'],
    'borderRadius': '10px',
    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
    'padding': '20px',
    'height': '100%'
}

def create_summary_card(title, value="N/A", subtitle=None, color='text', id=None):
    """Create a card for displaying summary values"""
    return dbc.Card([
        dbc.CardBody([
            html.H6(title, className="mb-2", style={'color': THEME['muted']}),
            html.H3(value, id=id, style={'color': THEME[color], 'fontSize': '1.8rem'}),
            html.P(subtitle, style={'color': THEME['muted']}) if subtitle else None,
        ])
    ], style=CARD_STYLE)

def create_asset_row(idx):
    """Create a row for asset input"""
    return dbc.Row([
        dbc.Col([
            dbc.Input(
                id={'type': 'asset-name', 'index': idx},
                type="text",
                placeholder="Asset name",
                style={'backgroundColor': THEME['surface'], 'color': THEME['text']}
            )
        ], width=3),
        dbc.Col([
            dbc.InputGroup([
                dbc.Input(
                    id={'type': 'asset-percentage', 'index': idx},
                    type="number",
                    min=0,
                    max=100,
                    placeholder="Portfolio %",
                    style={'backgroundColor': THEME['surface'], 'color': THEME['text']}
                ),
                dbc.InputGroupText("%")
            ])
        ], width=3),
        dbc.Col([
            dbc.InputGroup([
                dbc.Input(
                    id={'type': 'asset-yield', 'index': idx},
                    type="number",
                    min=0,
                    max=100,
                    placeholder="Dividend yield",
                    style={'backgroundColor': THEME['surface'], 'color': THEME['text']}
                ),
                dbc.InputGroupText("%")
            ])
        ], width=3),
        dbc.Col([
            dbc.Button(
                "×",  # Using × symbol for delete
                id={'type': 'delete-asset', 'index': idx},
                color="danger",
                size="sm",
                style={'fontSize': '1.2rem', 'padding': '0 8px'}
            )
        ], width=1),
    ], className="mb-2", id={'type': 'asset-row', 'index': idx})

# Create the main layout with tabs
layout = dbc.Container([
    html.H1("Investment Calculators", className="my-4", style={'color': THEME['text']}),
    
    dbc.Tabs([
        dbc.Tab(label="Growth Calculator", tab_id="growth-tab", children=[
            dbc.Row([
                # Input card
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Investment Parameters", 
                                   style={'color': THEME['text']}, 
                                   className="mb-4"),
                            dbc.Row([
                                # Initial Investment
                                dbc.Col([
                                    dbc.Label("Initial Investment (Kč)", style={'color': THEME['text']}),
                                    dbc.Input(
                                        id="initial-sum",
                                        type="number",
                                        value=100000,
                                        min=0,
                                        style={'backgroundColor': THEME['surface'], 'color': THEME['text']}
                                    )
                                ], md=6),
                                
                                # Monthly Investment
                                dbc.Col([
                                    dbc.Label("Monthly Investment (Kč)", style={'color': THEME['text']}),
                                    dbc.Input(
                                        id="monthly-investment",
                                        type="number",
                                        value=1000,
                                        min=0,
                                        style={'backgroundColor': THEME['surface'], 'color': THEME['text']}
                                    )
                                ], md=6),
                            ], className="mb-3"),
                            
                            dbc.Row([
                                # Annual Return
                                dbc.Col([
                                    dbc.Label("Annual Return (%)", style={'color': THEME['text']}),
                                    dbc.Input(
                                        id="annual-return",
                                        type="number",
                                        value=7,
                                        min=0,
                                        max=100,
                                        style={'backgroundColor': THEME['surface'], 'color': THEME['text']}
                                    )
                                ], md=6),
                                
                                # Years
                                dbc.Col([
                                    dbc.Label("Investment Period (Years)", style={'color': THEME['text']}),
                                    dbc.Input(
                                        id="years",
                                        type="number",
                                        value=10,
                                        min=1,
                                        max=50,
                                        style={'backgroundColor': THEME['surface'], 'color': THEME['text']}
                                    )
                                ], md=6),
                            ])
                        ])
                    ], style=CARD_STYLE)
                ], md=12, className="mb-4"),
                
                # Summary cards
                dbc.Col([
                    dbc.Row([
                        dbc.Col([
                            create_summary_card(
                                "Final Portfolio Value",
                                id="final-value",
                                color="success"
                            )
                        ], md=4),
                        dbc.Col([
                            create_summary_card(
                                "Total Invested",
                                id="total-invested",
                                color="primary"
                            )
                        ], md=4),
                        dbc.Col([
                            create_summary_card(
                                "Investment Gains",
                                id="total-gains",
                                color="text"
                            )
                        ], md=4),
                    ], className="mb-4"),
                ]),
                
                # Graph
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='investment-graph')
                        ])
                    ], style=CARD_STYLE)
                ], md=12),
            ])
        ]),
        
        dbc.Tab(label="Weighted Return Calculator", tab_id="weighted-tab", children=[
            dbc.Card([
                dbc.CardBody([
                    html.H3("Portfolio Weighted Return Calculator", 
                           style={'color': THEME['text']}, 
                           className="mb-4"),
                    
                    html.Div(id='asset-rows', children=[
                        create_asset_row(0)  # Start with one row
                    ]),
                    
                    dbc.Button(
                        "Add Asset",
                        id="add-asset",
                        color="primary",
                        className="mt-3"
                    ),
                    
                    html.Hr(style={'borderColor': THEME['muted']}),
                    
                    html.H4("Results", style={'color': THEME['text']}, className="mt-4"),
                    html.Div([
                        html.P([
                            "Total Portfolio Percentage: ",
                            html.Span("0%", id="total-percentage", 
                                    style={'color': THEME['success']})
                        ], style={'color': THEME['text']}),
                        html.P([
                            "Weighted Dividend Yield: ",
                            html.Span("0%", id="weighted-yield", 
                                    style={'color': THEME['success']})
                        ], style={'color': THEME['text']})
                    ])
                ])
            ], style=CARD_STYLE)
        ]),
        
        dbc.Tab(label="Dividend Tax Calculator", tab_id="dividend-tax-tab", children=[
            dbc.Card([
                dbc.CardBody([
                    html.H3("Dividend Tax Calculator", 
                           style={'color': THEME['text']}, 
                           className="mb-4"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Investment Amount (Kč)", style={'color': THEME['text']}),
                            dbc.Input(
                                id="dividend-amount",
                                type="number",
                                value=100000,
                                min=0,
                                style={'backgroundColor': THEME['surface'], 'color': THEME['text']}
                            )
                        ], md=4),
                        
                        dbc.Col([
                            dbc.Label("Dividend Tax Rate (%)", style={'color': THEME['text']}),
                            dbc.Input(
                                id="dividend-tax-rate",
                                type="number",
                                value=15,
                                min=0,
                                max=100,
                                style={'backgroundColor': THEME['surface'], 'color': THEME['text']}
                            )
                        ], md=4),
                        
                        dbc.Col([
                            dbc.Label("Dividend Yield (%)", style={'color': THEME['text']}),
                            dbc.Input(
                                id="dividend-yield-rate",
                                type="number",
                                value=4,
                                min=0,
                                max=100,
                                style={'backgroundColor': THEME['surface'], 'color': THEME['text']}
                            )
                        ], md=4)
                    ], className="mb-4"),
                    
                    html.Hr(style={'borderColor': THEME['muted']}),
                    
                    dbc.Row([
                        dbc.Col([
                            create_summary_card(
                                "Gross Dividend (Yearly)",
                                id="gross-dividend-yearly",
                                color="primary"
                            )
                        ], md=3),
                        dbc.Col([
                            create_summary_card(
                                "Tax Amount (Yearly)",
                                id="tax-amount-yearly",
                                color="text"
                            )
                        ], md=3),
                        dbc.Col([
                            create_summary_card(
                                "Net Dividend (Yearly)",
                                id="net-dividend-yearly",
                                color="success"
                            )
                        ], md=3),
                        dbc.Col([
                            create_summary_card(
                                "Net Dividend (Monthly)",
                                id="net-dividend-monthly",
                                color="success"
                            )
                        ], md=3),
                    ])
                ])
            ], style=CARD_STYLE)
        ])
    ], id="calculator-tabs", active_tab="growth-tab")
], fluid=True)

@callback(
    [Output('investment-graph', 'figure'),
     Output('final-value', 'children'),
     Output('total-invested', 'children'),
     Output('total-gains', 'children')],
    [Input('initial-sum', 'value'),
     Input('monthly-investment', 'value'),
     Input('annual-return', 'value'),
     Input('years', 'value')]
)
def update_growth_calculator(initial_sum, monthly_investment, annual_return, years):
    """Update investment projection graph and summary values."""
    
    # Handle invalid inputs
    if not all(v is not None and v >= 0 for v in [initial_sum, monthly_investment, annual_return, years]):
        return go.Figure(), "N/A", "N/A", "N/A"
    
    # Calculate growth
    df = calculate_investment_growth(initial_sum, monthly_investment, annual_return, years)
    
    # Get final values
    final_value = df['Value'].iloc[-1]
    total_invested = df['Invested'].iloc[-1]
    total_gains = df['Gains'].iloc[-1]
    
    # Create figure
    fig = go.Figure()
    
    # Add traces
    fig.add_trace(go.Scatter(
        x=df['Month'],
        y=df['Value'],
        name='Portfolio Value',
        line=dict(color='#2ecc71', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['Month'],
        y=df['Invested'],
        name='Amount Invested',
        line=dict(color='#3498db', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['Month'],
        y=df['Gains'],
        name='Investment Gains',
        line=dict(color='#f1c40f', width=3)
    ))
    
    # Update layout
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=600,
        title={
            'text': f'Investment Growth Projection ({annual_return}% Annual Return)',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis=dict(
            title='Year',
            gridcolor='rgba(128,128,128,0.2)',
            showgrid=True
        ),
        yaxis=dict(
            title='Value (Kč)',
            gridcolor='rgba(128,128,128,0.2)',
            showgrid=True,
            tickformat=',d'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=100)
    )
    
    return (
        fig,
        f"{final_value:,.0f} Kč",
        f"{total_invested:,.0f} Kč",
        f"{total_gains:,.0f} Kč"
    )

@callback(
    Output('asset-rows', 'children'),
    [Input('add-asset', 'n_clicks'),
     Input({'type': 'delete-asset', 'index': ALL}, 'n_clicks')],
    [State('asset-rows', 'children')],
    prevent_initial_call=True
)
def manage_asset_rows(add_clicks, delete_clicks, existing_rows):
    ctx = callback_context
    if not ctx.triggered:
        return existing_rows
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if trigger_id == 'add-asset.n_clicks':
        return existing_rows + [create_asset_row(len(existing_rows))]
    
    # Handle delete button clicks
    if '"type":"delete-asset"' in trigger_id:
        # Get the index of the clicked delete button
        deleted_idx = json.loads(trigger_id.split('.')[0])['index']
        # Keep all rows except the one with matching index
        remaining_rows = [
            row for row in existing_rows 
            if row['props']['id']['index'] != deleted_idx
        ]
        return remaining_rows  # Return rows as-is, no need to recreate them
    
    return existing_rows

@callback(
    [Output('total-percentage', 'children'),
     Output('weighted-yield', 'children')],
    [Input({'type': 'asset-percentage', 'index': ALL}, 'value'),
     Input({'type': 'asset-yield', 'index': ALL}, 'value')]
)
def calculate_weighted_return(percentages, yields):
    # Filter out None values
    valid_pairs = [(p or 0, y or 0) for p, y in zip(percentages, yields)]
    
    # Calculate totals
    total_percentage = sum(p for p, _ in valid_pairs)
    weighted_yield = sum(p * y / 100 for p, y in valid_pairs)
    
    return f"{total_percentage:.1f}%", f"{weighted_yield:.2f}%"

@callback(
    [Output('gross-dividend-yearly', 'children'),
     Output('tax-amount-yearly', 'children'),
     Output('net-dividend-yearly', 'children'),
     Output('net-dividend-monthly', 'children')],
    [Input('dividend-amount', 'value'),
     Input('dividend-tax-rate', 'value'),
     Input('dividend-yield-rate', 'value')]
)
def update_dividend_calculations(amount, tax_rate, yield_rate):
    if not all(v is not None and v >= 0 for v in [amount, tax_rate, yield_rate]):
        return "N/A", "N/A", "N/A", "N/A"
    
    # Calculate yearly dividend
    gross_yearly = amount * (yield_rate / 100)
    tax_yearly = gross_yearly * (tax_rate / 100)
    net_yearly = gross_yearly - tax_yearly
    net_monthly = net_yearly / 12
    
    return (
        f"{gross_yearly:,.2f} Kč",
        f"{tax_yearly:,.2f} Kč",
        f"{net_yearly:,.2f} Kč",
        f"{net_monthly:,.2f} Kč"
    )
