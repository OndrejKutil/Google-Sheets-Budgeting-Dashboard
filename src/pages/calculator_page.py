from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from investment_calc import calculate_investment_growth

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

# Layout
layout = dbc.Container([
    html.H1("Investment Calculator", className="my-4", style={'color': THEME['text']}),
    
    # Input Card
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
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
                        ], md=3),
                        
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
                        ], md=3),
                        
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
                        ], md=3),
                        
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
                        ], md=3),
                    ])
                ])
            ], style=CARD_STYLE)
        ])
    ], className="mb-4"),
    
    # Graph Card
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='investment-graph')
                ])
            ], style=CARD_STYLE)
        ])
    ])
], fluid=True)

@callback(
    Output('investment-graph', 'figure'),
    [Input('initial-sum', 'value'),
     Input('monthly-investment', 'value'),
     Input('annual-return', 'value'),
     Input('years', 'value')]
)
def update_graph(initial_sum, monthly_investment, annual_return, years):
    """Update investment projection graph based on inputs."""
    
    # Handle invalid inputs
    if not all(v is not None and v >= 0 for v in [initial_sum, monthly_investment, annual_return, years]):
        return go.Figure()
    
    # Calculate growth
    df = calculate_investment_growth(initial_sum, monthly_investment, annual_return, years)
    
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
    
    return fig
