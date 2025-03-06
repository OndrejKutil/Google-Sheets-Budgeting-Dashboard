from dash import html, dcc, callback, Input, Output, State, ALL, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from styles.theme import COLORS, CHART_THEME
from styles.common_styles import CARD_STYLE
import json
import pandas as pd

# Define the investment calculation function here since it might be missing
def calculate_investment_growth(initial_sum, monthly_investment, annual_return, years):
    try:
        # Input validation
        if initial_sum is None or monthly_investment is None or annual_return is None or years is None:
            return None
            
        # Convert to appropriate types
        initial_sum = float(initial_sum)
        monthly_investment = float(monthly_investment)
        annual_return = float(annual_return)
        years = int(years)
        
        # Calculate monthly return rate
        monthly_rate = (1 + annual_return / 100) ** (1/12) - 1
        
        # Initialize data storage
        months = years * 12
        data = []
        
        # Initial values
        current_value = initial_sum
        total_invested = initial_sum
        
        # Calculate for each month
        for month in range(1, months + 1):
            # Add monthly investment
            current_value += monthly_investment
            total_invested += monthly_investment
            
            # Apply monthly return
            current_value *= (1 + monthly_rate)
            
            # Record data at each year point
            if month % 12 == 0:
                year = month // 12
                data.append({
                    'Month': year,
                    'Value': round(current_value, 2),
                    'Invested': round(total_invested, 2),
                    'Gains': round(current_value - total_invested, 2)
                })
        
        return pd.DataFrame(data)
        
    except Exception as e:
        return None

def create_summary_card(title, value="N/A", subtitle=None, color='text', id=None):
    """Create a card for displaying summary values"""
    return dbc.Card([
        dbc.CardBody([
            html.H6(title, className="mb-2", style={'color': COLORS['text_muted']}),
            html.H3(value, id=id, style={'color': COLORS[color], 'fontSize': '1.8rem'}),
            html.P(subtitle, style={'color': COLORS['text_muted']}) if subtitle else None,
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
                style={'backgroundColor': COLORS['surface'], 'color': COLORS['text']}
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
                    style={'backgroundColor': COLORS['surface'], 'color': COLORS['text']}
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
                    style={'backgroundColor': COLORS['surface'], 'color': COLORS['text']}
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
    html.H1("Investment Calculators", className="my-4", style={'color': COLORS['text']}),

    dbc.Tabs([
        dbc.Tab(label="Growth Calculator", tab_id="growth-tab", children=[
            dbc.Row([
                # Input card
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Investment Parameters", 
                                   style={'color': COLORS['text']}, 
                                   className="mb-4"),
                            dbc.Row([
                                # Initial Investment
                                dbc.Col([
                                    dbc.Label("Initial Investment (Kč)", style={'color': COLORS['text']}),
                                    dbc.Input(
                                        id="initial-sum",
                                        type="number",
                                        value=100000,
                                        min=0,
                                        style={'backgroundColor': COLORS['surface'], 'color': COLORS['text']}
                                    )
                                ], md=6),

                                # Monthly Investment
                                dbc.Col([
                                    dbc.Label("Monthly Investment (Kč)", style={'color': COLORS['text']}),
                                    dbc.Input(
                                        id="monthly-investment",
                                        type="number",
                                        value=1000,
                                        min=0,
                                        style={'backgroundColor': COLORS['surface'], 'color': COLORS['text']}
                                    )
                                ], md=6),
                            ], className="mb-3"),

                            dbc.Row([
                                # Annual Return
                                dbc.Col([
                                    dbc.Label("Annual Return (%)", style={'color': COLORS['text']}),
                                    dbc.Input(
                                        id="annual-return",
                                        type="number",
                                        value=7,
                                        min=0,
                                        max=100,
                                        style={'backgroundColor': COLORS['surface'], 'color': COLORS['text']}
                                    )
                                ], md=6),

                                # Years
                                dbc.Col([
                                    dbc.Label("Investment Period (Years)", style={'color': COLORS['text']}),
                                    dbc.Input(
                                        id="years",
                                        type="number",
                                        value=10,
                                        min=1,
                                        max=50,
                                        style={'backgroundColor': COLORS['surface'], 'color': COLORS['text']}
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

                # Graphs section - Now with multiple graphs
                dbc.Col([
                    dbc.Tabs([
                        dbc.Tab(label="Growth Projection", children=[
                            dbc.Card([
                                dbc.CardBody([
                                    dcc.Graph(id='investment-graph')
                                ])
                            ], style=CARD_STYLE)
                        ]),
                        dbc.Tab(label="Annual Breakdown", children=[
                            dbc.Card([
                                dbc.CardBody([
                                    dcc.Graph(id='annual-contribution-graph')
                                ])
                            ], style=CARD_STYLE)
                        ]),
                        dbc.Tab(label="Compound Interest Effect", children=[
                            dbc.Card([
                                dbc.CardBody([
                                    dcc.Graph(id='compound-effect-graph')
                                ])
                            ], style=CARD_STYLE)
                        ])
                    ])
                ], md=12),
            ])
        ]),

        dbc.Tab(label="Weighted Return Calculator", tab_id="weighted-tab", children=[
            dbc.Card([
                dbc.CardBody([
                    html.H3("Portfolio Weighted Return Calculator", 
                           style={'color': COLORS['text']}, 
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

                    html.Hr(style={'borderColor': COLORS['text_muted']}),

                    html.H4("Results", style={'color': COLORS['text']}, className="mt-4"),
                    html.Div([
                        html.P([
                            "Total Portfolio Percentage: ",
                            html.Span("0%", id="total-percentage", 
                                    style={'color': COLORS['success']})
                        ], style={'color': COLORS['text']}),
                        html.P([
                            "Weighted Dividend Yield: ",
                            html.Span("0%", id="weighted-yield", 
                                    style={'color': COLORS['success']})
                        ], style={'color': COLORS['text']})
                    ]),

                    # Add visualization section
                    html.H4("Visualizations", style={'color': COLORS['text']}, className="mt-4"),
                    dbc.Tabs([
                        dbc.Tab(label="Portfolio Allocation", children=[
                            dbc.Card([
                                dbc.CardBody([
                                    dcc.Graph(id='portfolio-allocation-pie')
                                ])
                            ], style=CARD_STYLE)
                        ]),
                        dbc.Tab(label="Yield Comparison", children=[
                            dbc.Card([
                                dbc.CardBody([
                                    dcc.Graph(id='yield-comparison-bar')
                                ])
                            ], style=CARD_STYLE)
                        ])
                    ])
                ])
            ], style=CARD_STYLE)
        ]),

        dbc.Tab(label="Dividend Tax Calculator", tab_id="dividend-tax-tab", children=[
            dbc.Card([
                dbc.CardBody([
                    html.H3("Dividend Tax Calculator", 
                           style={'color': COLORS['text']}, 
                           className="mb-4"),

                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Investment Amount (Kč)", style={'color': COLORS['text']}),
                            dbc.Input(
                                id="dividend-amount",
                                type="number",
                                value=100000,
                                min=0,
                                style={'backgroundColor': COLORS['surface'], 'color': COLORS['text']}
                            )
                        ], md=4),

                        dbc.Col([
                            dbc.Label("Dividend Tax Rate (%)", style={'color': COLORS['text']}),
                            dbc.Input(
                                id="dividend-tax-rate",
                                type="number",
                                value=15,
                                min=0,
                                max=100,
                                style={'backgroundColor': COLORS['surface'], 'color': COLORS['text']}
                            )
                        ], md=4),

                        dbc.Col([
                            dbc.Label("Dividend Yield (%)", style={'color': COLORS['text']}),
                            dbc.Input(
                                id="dividend-yield-rate",
                                type="number",
                                value=4,
                                min=0,
                                max=100,
                                style={'backgroundColor': COLORS['surface'], 'color': COLORS['text']}
                            )
                        ], md=4)
                    ], className="mb-4"),

                    html.Hr(style={'borderColor': COLORS['text_muted']}),

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
                    ]),

                    # Add visualization section
                    html.Hr(style={'borderColor': COLORS['text_muted']}),
                    html.H4("Visualizations", style={'color': COLORS['text']}, className="mt-4"),
                    dbc.Tabs([
                        dbc.Tab(label="Tax Impact", children=[
                            dbc.Card([
                                dbc.CardBody([
                                    dcc.Graph(id='tax-impact-graph')
                                ])
                            ], style=CARD_STYLE)
                        ]),
                        dbc.Tab(label="Monthly Income Projection", children=[
                            dbc.Card([
                                dbc.CardBody([
                                    dcc.Graph(id='monthly-income-projection')
                                ])
                            ], style=CARD_STYLE)
                        ])
                    ])
                ])
            ], style=CARD_STYLE)
        ])
    ], id="calculator-tabs", active_tab="growth-tab")
], fluid=True)

@callback(
    [Output('investment-graph', 'figure'),
     Output('annual-contribution-graph', 'figure'),
     Output('compound-effect-graph', 'figure'),
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
    
    
    try:
        # Handle invalid inputs
        if None in [initial_sum, monthly_investment, annual_return, years]:
            raise ValueError("Invalid input values - None values detected")
            
        # Convert inputs to appropriate types
        initial_sum = float(initial_sum) if initial_sum else 0
        monthly_investment = float(monthly_investment) if monthly_investment else 0
        annual_return = float(annual_return) if annual_return else 0
        years = int(years) if years else 0
        
        
        if not all(v >= 0 for v in [initial_sum, monthly_investment, annual_return, years]):
            raise ValueError("Input values must be non-negative")
        
        # Calculate growth
        df = calculate_investment_growth(initial_sum, monthly_investment, annual_return, years)
        
        if df is None or df.empty:
            raise ValueError("No data calculated")
            
        
        # Get final values
        final_value = df['Value'].iloc[-1]
        total_invested = df['Invested'].iloc[-1]
        total_gains = df['Gains'].iloc[-1]
        
        
        # Create the main investment graph (same as before)
        main_fig = go.Figure()
        
        # Add stacked bars
        main_fig.add_trace(go.Bar(
            x=df['Month'],
            y=df['Invested'],
            name='Amount Invested',
            marker_color=COLORS['primary'],
            hovertemplate='Amount Invested: %{y:,.0f} Kč<br>Year: %{x:.0f}<extra></extra>'
        ))
        
        main_fig.add_trace(go.Bar(
            x=df['Month'],
            y=df['Gains'],
            name='Investment Gains',
            marker_color=COLORS['purple'],
            hovertemplate='Investment Gains: %{y:,.0f} Kč<br>Year: %{x:.0f}<extra></extra>'
        ))
        
        # Add a line for the total value
        main_fig.add_trace(go.Scatter(
            x=df['Month'],
            y=df['Value'],
            name='Total Value',
            line=dict(color=COLORS['success'], width=3),
            hovertemplate='Total Value: %{y:,.0f} Kč<br>Year: %{x:.0f}<extra></extra>'
        ))
        
        # Update layout for main graph
        main_fig.update_layout(
            barmode='stack',
            template='plotly_dark',
            paper_bgcolor=CHART_THEME['paper_bgcolor'],
            plot_bgcolor=CHART_THEME['bgcolor'],
            height=600,
            title={
                'text': f'Investment Growth Projection ({annual_return}% Annual Return)',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': CHART_THEME['title_font_size'], 'color': CHART_THEME['font_color']}
            },
            xaxis=dict(
                title='Year',
                gridcolor=CHART_THEME['axis']['gridcolor'],
                linecolor=CHART_THEME['axis']['linecolor'],
                showgrid=True,
                dtick=1,
                color=CHART_THEME['axis']['color']
            ),
            yaxis=dict(
                title='Value (Kč)',
                gridcolor=CHART_THEME['axis']['gridcolor'],
                linecolor=CHART_THEME['axis']['linecolor'],
                showgrid=True,
                tickformat=',d',
                color=CHART_THEME['axis']['color']
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color=CHART_THEME['font_color'])
            ),
            margin=dict(t=100),
            hoverlabel=dict(
                bgcolor=COLORS['surface'],
                font_size=14,
                font_family='"Segoe UI", Arial, sans-serif'
            )
        )
        
        # Create the annual contribution breakdown graph
        annual_contrib_fig = go.Figure()
        
        # Add annual contributions
        annual_contrib_data = pd.DataFrame({
            'Year': df['Month'],
            'Annual Contribution': [monthly_investment * 12] * len(df),
            'Annual Growth': df['Value'].diff().fillna(df['Value'] - initial_sum - monthly_investment) - monthly_investment * 12
        })
        
        annual_contrib_fig.add_trace(go.Bar(
            x=annual_contrib_data['Year'],
            y=annual_contrib_data['Annual Contribution'],
            name='Annual Contribution',
            marker_color=COLORS['primary'],
            hovertemplate='Annual Contribution: %{y:,.0f} Kč<br>Year: %{x:.0f}<extra></extra>'
        ))
        
        annual_contrib_fig.add_trace(go.Bar(
            x=annual_contrib_data['Year'],
            y=annual_contrib_data['Annual Growth'],
            name='Annual Growth',
            marker_color=COLORS['success'],
            hovertemplate='Annual Growth: %{y:,.0f} Kč<br>Year: %{x:.0f}<extra></extra>'
        ))
        
        annual_contrib_fig.update_layout(
            barmode='group',
            template='plotly_dark',
            paper_bgcolor=CHART_THEME['paper_bgcolor'],
            plot_bgcolor=CHART_THEME['bgcolor'],
            height=600,
            title={
                'text': 'Annual Contributions vs. Growth',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': CHART_THEME['title_font_size'], 'color': CHART_THEME['font_color']}
            },
            xaxis=dict(
                title='Year',
                gridcolor=CHART_THEME['axis']['gridcolor'],
                linecolor=CHART_THEME['axis']['linecolor'],
                showgrid=True,
                dtick=1,
                color=CHART_THEME['axis']['color']
            ),
            yaxis=dict(
                title='Value (Kč)',
                gridcolor=CHART_THEME['axis']['gridcolor'],
                linecolor=CHART_THEME['axis']['linecolor'],
                showgrid=True,
                tickformat=',d',
                color=CHART_THEME['axis']['color']
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color=CHART_THEME['font_color'])
            ),
            margin=dict(t=100),
            hoverlabel=dict(
                bgcolor=COLORS['surface'],
                font_size=14,
                font_family='"Segoe UI", Arial, sans-serif'
            )
        )
        
        # Create the compound interest effect graph
        compound_effect_fig = go.Figure()
        
        # Calculate no-compound scenario (just sum of investments)
        no_compound_value = initial_sum + (monthly_investment * 12 * df['Month'])
        
        compound_effect_fig.add_trace(go.Scatter(
            x=df['Month'],
            y=no_compound_value,
            name='Without Compound Interest',
            line=dict(color=COLORS['text_muted'], width=2, dash='dash'),
            hovertemplate='Without Compound: %{y:,.0f} Kč<br>Year: %{x:.0f}<extra></extra>'
        ))
        
        compound_effect_fig.add_trace(go.Scatter(
            x=df['Month'],
            y=df['Value'],
            name='With Compound Interest',
            line=dict(color=COLORS['success'], width=3),
            hovertemplate='With Compound: %{y:,.0f} Kč<br>Year: %{x:.0f}<extra></extra>'
        ))
        
        compound_effect_fig.add_trace(go.Scatter(
            x=df['Month'],
            y=df['Value'] - no_compound_value,
            name='Compound Interest Effect',
            line=dict(color=COLORS['purple'], width=2, dash='dot'),
            hovertemplate='Compound Effect: %{y:,.0f} Kč<br>Year: %{x:.0f}<extra></extra>'
        ))
        
        compound_effect_fig.update_layout(
            template='plotly_dark',
            paper_bgcolor=CHART_THEME['paper_bgcolor'],
            plot_bgcolor=CHART_THEME['bgcolor'],
            height=600,
            title={
                'text': f'Power of Compound Interest ({annual_return}% Annual Return)',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': CHART_THEME['title_font_size'], 'color': CHART_THEME['font_color']}
            },
            xaxis=dict(
                title='Year',
                gridcolor=CHART_THEME['axis']['gridcolor'],
                linecolor=CHART_THEME['axis']['linecolor'],
                showgrid=True,
                dtick=1,
                color=CHART_THEME['axis']['color']
            ),
            yaxis=dict(
                title='Value (Kč)',
                gridcolor=CHART_THEME['axis']['gridcolor'],
                linecolor=CHART_THEME['axis']['linecolor'],
                showgrid=True,
                tickformat=',d',
                color=CHART_THEME['axis']['color']
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color=CHART_THEME['font_color'])
            ),
            margin=dict(t=100),
            hoverlabel=dict(
                bgcolor=COLORS['surface'],
                font_size=14,
                font_family='"Segoe UI", Arial, sans-serif'
            )
        )
        
        
        return (
            main_fig,
            annual_contrib_fig,
            compound_effect_fig,
            f"{final_value:,.0f} Kč",
            f"{total_invested:,.0f} Kč",
            f"{total_gains:,.0f} Kč"
        )
        
    except Exception as e:
        
        # Return empty figures and N/A values
        empty_fig = go.Figure()
        empty_fig.update_layout(
            paper_bgcolor=CHART_THEME['paper_bgcolor'],
            plot_bgcolor=CHART_THEME['bgcolor'],
            height=600,
            title={
                'text': 'No data to display',
                'y': 0.5,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'middle',
                'font': {'size': CHART_THEME['title_font_size'], 'color': CHART_THEME['font_color']}
            }
        )
        
        return (
            empty_fig,
            empty_fig,
            empty_fig,
            "N/A",
            "N/A",
            "N/A"
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
    [Output('portfolio-allocation-pie', 'figure'),
     Output('yield-comparison-bar', 'figure'),
     Output('total-percentage', 'children'),
     Output('weighted-yield', 'children')],
    [Input({'type': 'asset-name', 'index': ALL}, 'value'),
     Input({'type': 'asset-percentage', 'index': ALL}, 'value'),
     Input({'type': 'asset-yield', 'index': ALL}, 'value')]
)
def calculate_weighted_return(asset_names, percentages, yields):
    try:
        # Prepare data for visualization
        names = [n if n else f"Asset {i+1}" for i, n in enumerate(asset_names)]
        
        # Filter out None values
        valid_data = [(name, float(p) if p is not None else 0, float(y) if y is not None else 0) 
                      for name, p, y in zip(names, percentages, yields)]
        
        # Calculate totals
        total_percentage = sum(p for _, p, _ in valid_data)
        weighted_yield = sum(p * y / 100 for _, p, y in valid_data)
        
        # Create portfolio allocation pie chart
        allocation_fig = go.Figure()
        
        # Only include assets with non-zero percentages
        pie_data = [(name, p) for name, p, _ in valid_data if p > 0]
        
        if pie_data:
            allocation_fig.add_trace(go.Pie(
                labels=[name for name, _ in pie_data],
                values=[p for _, p in pie_data],
                textinfo='label+percent',
                marker_colors=[COLORS['primary'], COLORS['success'], COLORS['danger'], 
                               COLORS['info'], COLORS['purple']]
            ))
        
        allocation_fig.update_layout(
            template='plotly_dark',
            paper_bgcolor=CHART_THEME['paper_bgcolor'],
            plot_bgcolor=CHART_THEME['bgcolor'],
            height=400,
            title={
                'text': 'Portfolio Allocation',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': CHART_THEME['title_font_size'], 'color': CHART_THEME['font_color']}
            }
        )
        
        # Create yield comparison bar chart
        yield_fig = go.Figure()
        
        # Only include assets with names and non-zero percentages
        bar_data = [(name, p, y) for name, p, y in valid_data if p > 0]
        
        if bar_data:
            yield_fig.add_trace(go.Bar(
                x=[name for name, _, _ in bar_data],
                y=[y for _, _, y in bar_data],
                text=[f"{y:.2f}%" for _, _, y in bar_data],
                textposition='auto',
                marker_color=COLORS['primary'],
                name='Individual Yield'
            ))
            
            # Add weighted average line
            if weighted_yield > 0:
                yield_fig.add_trace(go.Scatter(
                    x=[name for name, _, _ in bar_data],
                    y=[weighted_yield] * len(bar_data),
                    mode='lines',
                    line=dict(color=COLORS['danger'], width=2, dash='dash'),
                    name=f'Weighted Avg: {weighted_yield:.2f}%'
                ))
        
        yield_fig.update_layout(
            template='plotly_dark',
            paper_bgcolor=CHART_THEME['paper_bgcolor'],
            plot_bgcolor=CHART_THEME['bgcolor'],
            height=400,
            title={
                'text': 'Dividend Yield by Asset',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': CHART_THEME['title_font_size'], 'color': CHART_THEME['font_color']}
            },
            xaxis=dict(
                title='Asset',
                gridcolor=CHART_THEME['axis']['gridcolor'],
                linecolor=CHART_THEME['axis']['linecolor'],
                color=CHART_THEME['axis']['color']
            ),
            yaxis=dict(
                title='Yield (%)',
                gridcolor=CHART_THEME['axis']['gridcolor'],
                linecolor=CHART_THEME['axis']['linecolor'],
                color=CHART_THEME['axis']['color']
            )
        )
        
        return allocation_fig, yield_fig, f"{total_percentage:.1f}%", f"{weighted_yield:.2f}%"
    except Exception as e:
        # Return empty figures and default values
        empty_fig = go.Figure()
        empty_fig.update_layout(
            paper_bgcolor=CHART_THEME['paper_bgcolor'],
            plot_bgcolor=CHART_THEME['bgcolor'],
            height=400
        )
        return empty_fig, empty_fig, "0.0%", "0.00%"

@callback(
    [Output('tax-impact-graph', 'figure'),
     Output('monthly-income-projection', 'figure'),
     Output('gross-dividend-yearly', 'children'),
     Output('tax-amount-yearly', 'children'),
     Output('net-dividend-yearly', 'children'),
     Output('net-dividend-monthly', 'children')],
    [Input('dividend-amount', 'value'),
     Input('dividend-tax-rate', 'value'),
     Input('dividend-yield-rate', 'value')]
)
def update_dividend_calculations(amount, tax_rate, yield_rate):
    try:
        if None in [amount, tax_rate, yield_rate]:
            raise ValueError("Invalid input values")
        
        # Convert inputs to appropriate types
        amount = float(amount)
        tax_rate = float(tax_rate)
        yield_rate = float(yield_rate)
        
        if not all(v >= 0 for v in [amount, tax_rate, yield_rate]):
            raise ValueError("Input values must be non-negative")
        
        # Calculate yearly dividend
        gross_yearly = amount * (yield_rate / 100)
        tax_yearly = gross_yearly * (tax_rate / 100)
        net_yearly = gross_yearly - tax_yearly
        net_monthly = net_yearly / 12
        
        # Create tax impact graph (waterfall chart)
        tax_fig = go.Figure()
        
        tax_fig.add_trace(go.Waterfall(
            name="Tax Impact",
            orientation="v",
            measure=["absolute", "relative", "total"],
            x=["Gross Dividend", "Tax", "Net Dividend"],
            text=[f"{gross_yearly:,.2f} Kč", f"-{tax_yearly:,.2f} Kč", f"{net_yearly:,.2f} Kč"],
            textposition="outside",
            y=[gross_yearly, -tax_yearly, 0],
            connector={"line": {"color": COLORS['border']}},
            decreasing={"marker": {"color": COLORS['danger']}},
            increasing={"marker": {"color": COLORS['success']}},
            totals={"marker": {"color": COLORS['primary']}}
        ))
        
        tax_fig.update_layout(
            template='plotly_dark',
            paper_bgcolor=CHART_THEME['paper_bgcolor'],
            plot_bgcolor=CHART_THEME['bgcolor'],
            height=400,
            title={
                'text': f'Tax Impact on {yield_rate}% Dividend Yield',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': CHART_THEME['title_font_size'], 'color': CHART_THEME['font_color']}
            },
            xaxis=dict(
                title='',
                gridcolor=CHART_THEME['axis']['gridcolor'],
                linecolor=CHART_THEME['axis']['linecolor'],
                color=CHART_THEME['axis']['color']
            ),
            yaxis=dict(
                title='Amount (Kč)',
                gridcolor=CHART_THEME['axis']['gridcolor'],
                linecolor=CHART_THEME['axis']['linecolor'],
                color=CHART_THEME['axis']['color']
            ),
            showlegend=False
        )
        
        # Create monthly income projection with different investment amounts
        monthly_projection_fig = go.Figure()
        
        # Show projection for different investment amounts
        multipliers = [0.5, 1, 2, 5, 10]
        amounts = [amount * m for m in multipliers]
        monthly_incomes = [(a * (yield_rate / 100) * (1 - tax_rate / 100)) / 12 for a in amounts]
        
        monthly_projection_fig.add_trace(go.Bar(
            x=[f"{m}x ({a:,.0f} Kč)" for m, a in zip(multipliers, amounts)],
            y=monthly_incomes,
            text=[f"{income:,.0f} Kč" for income in monthly_incomes],
            textposition="auto",
            marker_color=COLORS['success']
        ))
        
        monthly_projection_fig.update_layout(
            template='plotly_dark',
            paper_bgcolor=CHART_THEME['paper_bgcolor'],
            plot_bgcolor=CHART_THEME['bgcolor'],
            height=400,
            title={
                'text': 'Monthly Dividend Income Projection',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': CHART_THEME['title_font_size'], 'color': CHART_THEME['font_color']}
            },
            xaxis=dict(
                title='Investment Amount (Multiple of Current)',
                gridcolor=CHART_THEME['axis']['gridcolor'],
                linecolor=CHART_THEME['axis']['linecolor'],
                color=CHART_THEME['axis']['color']
            ),
            yaxis=dict(
                title='Monthly Income (Kč)',
                gridcolor=CHART_THEME['axis']['gridcolor'],
                linecolor=CHART_THEME['axis']['linecolor'],
                color=CHART_THEME['axis']['color']
            )
        )
        
        return (
            tax_fig,
            monthly_projection_fig,
            f"{gross_yearly:,.2f} Kč",
            f"{tax_yearly:,.2f} Kč",
            f"{net_yearly:,.2f} Kč",
            f"{net_monthly:,.2f} Kč"
        )
    except Exception as e:
        # Return empty figures and N/A values
        empty_fig = go.Figure()
        empty_fig.update_layout(
            paper_bgcolor=CHART_THEME['paper_bgcolor'],
            plot_bgcolor=CHART_THEME['bgcolor'],
            height=400
        )
        return empty_fig, empty_fig, "N/A", "N/A", "N/A", "N/A"
