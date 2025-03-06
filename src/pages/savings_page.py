from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np
from data_fetch import get_transactions
from get_categories import get_all_categories_api
from analysis import sum_values_by_criteria
import plotly.graph_objects as go
from datetime import datetime
from styles.theme import COLORS, TEXT_STYLES, CHART_THEME  # Add CHART_THEME to imports

def create_stat_card(title, value, color="primary", is_percentage=False):
    """Create a statistics card with consistent styling."""
    return dbc.Card([
        dbc.CardBody([
            html.H6(title, style={'color': COLORS['text_muted']}),  # Updated style
            html.H4(
                f"{value:,.2f}{'%' if is_percentage else ' Kč'}",
                style={'color': COLORS[color], 'whiteSpace': 'nowrap'}  # Updated style
            )
        ], className="p-2")
    ], className="h-100")

layout = dbc.Container([
    html.H1("Savings & Investments Overview", style={'color': COLORS['text']}, className="my-4"),
    
    # Top row - All statistics cards
    dbc.Row([
        dbc.Col([html.Div(id="total-savings-card")], xs=12, sm=6, md=3, className="mb-3"),
        dbc.Col([html.Div(id="total-investments-card")], xs=12, sm=6, md=3, className="mb-3"),
        dbc.Col([html.Div(id="savings-ratio-card")], xs=12, sm=6, md=3, className="mb-3"),
        dbc.Col([html.Div(id="investment-ratio-card")], xs=12, sm=6, md=3, className="mb-3"),
    ], className="mb-4"),
    
    # First chart row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Monthly Savings & Investments", 
                           style={'color': COLORS['text']},  # Updated style
                           className="text-center mb-4"),
                    dbc.Spinner(dcc.Graph(id='savings-chart', figure={}))
                ])
            ])
        ], md=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Monthly Ratios (%)", 
                           style={'color': COLORS['text']},  # Updated style
                           className="text-center mb-4"),
                    dbc.Spinner(dcc.Graph(id='ratio-chart', figure={}))
                ])
            ])
        ], md=6)
    ], className="mb-4"),
    
    # Second chart row - New charts
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Cumulative Growth", 
                           style={'color': COLORS['text']},  # Updated style
                           className="text-center mb-4"),
                    dbc.Spinner(dcc.Graph(id='cumulative-chart', figure={}))
                ])
            ])
        ], md=8),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Monthly Performance", 
                           style={'color': COLORS['text']},  # Updated style
                           className="text-center mb-4"),
                    dbc.Spinner(dcc.Graph(id='performance-chart', figure={}))
                ])
            ])
        ], md=4)
    ])
], fluid=True, style={'backgroundColor': COLORS['background']})  # Added background color

@callback(
    [Output('savings-chart', 'figure'),
     Output('ratio-chart', 'figure'),
     Output('cumulative-chart', 'figure'),
     Output('performance-chart', 'figure'),
     Output('total-savings-card', 'children'),
     Output('total-investments-card', 'children'),
     Output('savings-ratio-card', 'children'),
     Output('investment-ratio-card', 'children')],
    [Input('overview-tabs', 'active_tab')]
)
def update_savings_view(active_tab):
    """Update all dashboard components."""
    try:
        SPREADSHEET_NAME = "Budget tracker 2025"
        df = pd.DataFrame(get_transactions(SPREADSHEET_NAME, "transactions"))
        income_cats, _, saving_cats, investing_cats = get_all_categories_api(SPREADSHEET_NAME)
        
        # Calculate total income
        total_income = sum_values_by_criteria(df, 'VALUE', CATEGORY=income_cats)
        
        # Calculate statistics
        total_savings = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=saving_cats))
        total_investments = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=investing_cats))
        
        # Calculate ratios
        savings_ratio = (total_savings / total_income) if total_income > 0 else 0
        investment_ratio = (total_investments / total_income) if total_income > 0 else 0
        
        # Monthly calculations
        all_months = ['January', 'February', 'March', 'April', 'May', 'June', 
                     'July', 'August', 'September', 'October', 'November', 'December']
        monthly_data = []
        
        for month in all_months:
            month_income = sum_values_by_criteria(df, 'VALUE', CATEGORY=income_cats, MONTH=month)
            month_savings = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=saving_cats, MONTH=month))
            month_investments = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=investing_cats, MONTH=month))
            
            # Calculate monthly ratios
            month_savings_ratio = (month_savings / month_income) if month_income > 0 else 0
            month_investment_ratio = (month_investments / month_income) if month_income > 0 else 0
            
            monthly_data.append({
                'Month': month,
                'Savings': month_savings,
                'Investments': month_investments,
                'Savings Ratio': month_savings_ratio * 100,  # Convert to percentage
                'Investment Ratio': month_investment_ratio * 100  # Convert to percentage
            })
        
        monthly_df = pd.DataFrame(monthly_data)
        
        # Calculate averages
        active_months = np.sum((monthly_df['Savings'] > 0) | (monthly_df['Investments'] > 0))
        monthly_savings_avg = total_savings / active_months if active_months > 0 else 0
        monthly_investments_avg = total_investments / active_months if active_months > 0 else 0
        
        # Create cumulative data
        monthly_df['Cumulative Savings'] = monthly_df['Savings'].cumsum()
        monthly_df['Cumulative Investments'] = monthly_df['Investments'].cumsum()
        monthly_df['Total Wealth'] = monthly_df['Cumulative Savings'] + monthly_df['Cumulative Investments']
        
        # Calculate month-over-month changes
        monthly_df['MoM Growth'] = monthly_df['Total Wealth'].pct_change() * 100
        
        # Create charts
        fig1 = create_monthly_chart(monthly_df)
        fig2 = create_ratio_chart(monthly_df)
        fig3 = create_cumulative_chart(monthly_df)
        fig4 = create_performance_chart(monthly_df)
        
        return (
            fig1, fig2, fig3, fig4,
            create_stat_card("Total Savings", total_savings, "info"),
            create_stat_card("Total Investments", total_investments, "success"),
            create_stat_card("Savings Ratio", savings_ratio * 100, "info", is_percentage=True),
            create_stat_card("Investment Ratio", investment_ratio * 100, "success", is_percentage=True)
        )
        
    except Exception as e:
        print(f"Error updating savings view: {e}")
        empty_card = create_stat_card("Error", 0, "danger")
        return {}, {}, {}, {}, empty_card, empty_card, empty_card, empty_card

def create_monthly_chart(df):
    """Create monthly savings and investments comparison chart."""
    fig = go.Figure()
    
    # Add savings bars
    fig.add_trace(go.Bar(
        name='Savings',
        x=df['Month'],
        y=df['Savings'],
        marker_color='rgb(46, 204, 113)'
    ))
    
    # Add investment bars
    fig.add_trace(go.Bar(
        name='Investments',
        x=df['Month'],
        y=df['Investments'],
        marker_color='rgb(52, 152, 219)'
    ))
    
    fig.update_layout(
        barmode='group',
        paper_bgcolor=CHART_THEME['bgcolor'],
        plot_bgcolor=CHART_THEME['bgcolor'],
        height=400,
        yaxis_title="Amount (Kč)",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=CHART_THEME['font_color'])  # Added font color
        ),
        margin=dict(t=30, r=10, b=50, l=50),
        xaxis=dict(
            color=CHART_THEME['font_color'],
            gridcolor=CHART_THEME['axis']['gridcolor'],
            linecolor=CHART_THEME['axis']['linecolor']
        ),
        yaxis=dict(
            color=CHART_THEME['font_color'],
            gridcolor=CHART_THEME['axis']['gridcolor'],
            linecolor=CHART_THEME['axis']['linecolor']
        ),
        font=dict(color=CHART_THEME['font_color'])  # Added global font color
    )
    
    return fig

def create_ratio_chart(df):
    """Create monthly ratios comparison chart."""
    fig = go.Figure()
    
    # Add savings ratio line
    fig.add_trace(go.Scatter(
        name='Savings Ratio',
        x=df['Month'],
        y=df['Savings Ratio'],
        mode='lines+markers',
        line=dict(color='rgb(46, 204, 113)', width=3),
        marker=dict(size=8)
    ))
    
    # Add investment ratio line
    fig.add_trace(go.Scatter(
        name='Investment Ratio',
        x=df['Month'],
        y=df['Investment Ratio'],
        mode='lines+markers',
        line=dict(color='rgb(52, 152, 219)', width=3),
        marker=dict(size=8)
    ))
    
    # Add target lines
    fig.add_hline(y=20, line_dash="dash", line_color="rgba(255, 255, 255, 0.3)",
                  annotation_text="Savings Target")
    fig.add_hline(y=10, line_dash="dash", line_color="rgba(255, 255, 255, 0.3)",
                  annotation_text="Investment Target")
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        yaxis_title="Ratio (%)",
        yaxis_tickformat='.1f',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=CHART_THEME['font_color'])  # Added font color
        ),
        margin=dict(t=30, r=10, b=50, l=50),
        xaxis=dict(
            color=CHART_THEME['font_color'],
            gridcolor=CHART_THEME['axis']['gridcolor'],
            linecolor=CHART_THEME['axis']['linecolor']
        ),
        yaxis=dict(
            color=CHART_THEME['font_color'],
            gridcolor=CHART_THEME['axis']['gridcolor'],
            linecolor=CHART_THEME['axis']['linecolor']
        ),
        font=dict(color=CHART_THEME['font_color'])  # Added global font color
    )
    
    return fig

def create_cumulative_chart(df):
    """Create stacked area chart showing cumulative growth."""
    fig = go.Figure()
    
    # Add Savings area
    fig.add_trace(go.Scatter(
        x=df['Month'],
        y=df['Cumulative Savings'],
        name='Savings',
        fill='tonexty',
        mode='lines',
        line=dict(width=0.5, color='rgb(46, 204, 113)'),
        stackgroup='one',
        hovertemplate="<b>Savings</b>: %{y:,.0f} Kč<extra></extra>"
    ))
    
    # Add Investments area
    fig.add_trace(go.Scatter(
        x=df['Month'],
        y=df['Cumulative Investments'],
        name='Investments',
        fill='tonexty',
        mode='lines',
        line=dict(width=0.5, color='rgb(52, 152, 219)'),
        stackgroup='one',
        hovertemplate="<b>Investments</b>: %{y:,.0f} Kč<extra></extra>"
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        hovermode='x unified',
        yaxis_title="Cumulative Amount (Kč)",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=CHART_THEME['font_color'])  # Added font color
        ),
        margin=dict(t=30, r=10, b=50, l=50),
        xaxis=dict(
            color=CHART_THEME['font_color'],
            gridcolor=CHART_THEME['axis']['gridcolor'],
            linecolor=CHART_THEME['axis']['linecolor']
        ),
        yaxis=dict(
            color=CHART_THEME['font_color'],
            gridcolor=CHART_THEME['axis']['gridcolor'],
            linecolor=CHART_THEME['axis']['linecolor']
        ),
        font=dict(color=CHART_THEME['font_color']),  # Added global font color
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_color="black"
        )
    )
    
    return fig

def create_performance_chart(df):
    """Create performance metrics chart."""
    fig = go.Figure()
    
    # Add MoM growth bars
    fig.add_trace(go.Bar(
        x=df['Month'],
        y=df['MoM Growth'],
        name='Month-over-Month Growth',
        marker_color=np.where(df['MoM Growth'] >= 0, 'rgb(46, 204, 113)', 'rgb(231, 76, 60)'),
        hovertemplate='%{y:.1f}%<extra></extra>'
    ))
    
    # Add target line
    fig.add_hline(
        y=10,  # Assuming 10% monthly growth target
        line_dash="dash",
        line_color="rgba(255, 255, 255, 0.5)",
        annotation_text="Target"
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        showlegend=False,
        yaxis_title="Growth Rate (%)",
        yaxis_tickformat='.1f',
        margin=dict(t=30, r=10, b=50, l=50),
        xaxis=dict(
            color=CHART_THEME['font_color'],
            gridcolor=CHART_THEME['axis']['gridcolor'],
            linecolor=CHART_THEME['axis']['linecolor']
        ),
        yaxis=dict(
            color=CHART_THEME['font_color'],
            gridcolor=CHART_THEME['axis']['gridcolor'],
            linecolor=CHART_THEME['axis']['linecolor']
        ),
        font=dict(color=CHART_THEME['font_color'])  # Added global font color
    )
    
    return fig
