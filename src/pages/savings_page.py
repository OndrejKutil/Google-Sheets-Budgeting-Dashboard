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
        
        # Ensure HISA_FUND column exists, add it if missing
        if 'HISA_FUND' not in df.columns:
            df['HISA_FUND'] = ''
            
        # Calculate total income
        total_income = sum_values_by_criteria(df, 'VALUE', CATEGORY=income_cats)
        
        # Calculate statistics
        # Regular savings (negative values)
        savings_deposits = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=saving_cats, 
                                                     VALUE_CONDITION='< 0'))
        
        # Create withdrawal mask: HISA_FUND populated + positive value + TYPE is 'income'
        withdrawal_mask = (df['HISA_FUND'].notna() & 
                          (df['HISA_FUND'].astype(str) != '') & 
                          (df['TYPE'] == 'income'))
        
        # Get withdrawals from savings funds
        df_withdrawals = df[withdrawal_mask].copy()
        savings_withdrawals = sum_values_by_criteria(df_withdrawals, 'VALUE', VALUE_CONDITION='> 0')
        
        # Net savings calculation
        total_savings = savings_deposits - savings_withdrawals
        
        # Calculate total investments
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
            
            # Regular savings (negative values)
            month_savings_deposits = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=saving_cats, 
                                                              MONTH=month, VALUE_CONDITION='< 0'))
            
            # Withdrawals from savings (positive values with HISA_FUND populated)
            month_mask = withdrawal_mask & (df['MONTH'] == month)
            month_df_withdrawals = df[month_mask]
            month_savings_withdrawals = sum_values_by_criteria(month_df_withdrawals, 'VALUE', VALUE_CONDITION='> 0')
            
            # Net savings
            month_net_savings = month_savings_deposits - month_savings_withdrawals
            
            month_investments = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=investing_cats, MONTH=month))
            
            # Calculate monthly ratios (prevent division by zero)
            month_savings_ratio = (month_net_savings / month_income) if month_income > 0 else 0
            month_investment_ratio = (month_investments / month_income) if month_income > 0 else 0
            
            monthly_data.append({
                'Month': month,
                'Savings': month_net_savings,
                'Savings Deposits': month_savings_deposits,
                'Savings Withdrawals': month_savings_withdrawals,
                'Investments': month_investments,
                'Savings Ratio': month_savings_ratio * 100,  # Convert to percentage
                'Investment Ratio': month_investment_ratio * 100  # Convert to percentage
            })
        
        monthly_df = pd.DataFrame(monthly_data)
        
        # Calculate averages
        active_months = np.sum((monthly_df['Savings'] != 0) | (monthly_df['Investments'] > 0))
        active_months = max(active_months, 1)  # Avoid division by zero
        monthly_savings_avg = total_savings / active_months
        monthly_investments_avg = total_investments / active_months
        
        # Create cumulative data with net savings
        monthly_df['Cumulative Savings'] = monthly_df['Savings'].cumsum()
        monthly_df['Cumulative Investments'] = monthly_df['Investments'].cumsum()
        monthly_df['Total Wealth'] = monthly_df['Cumulative Savings'] + monthly_df['Cumulative Investments']
        
        # Calculate month-over-month changes
        monthly_df['MoM Growth'] = monthly_df['Total Wealth'].pct_change() * 100
        monthly_df['MoM Growth'] = monthly_df['MoM Growth'].fillna(0)  # Replace NaN with 0 for first month
        
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
        print(f"Error updating savings view: {str(e)}")
        import traceback
        traceback.print_exc()
        empty_card = create_stat_card("Error", 0, "danger")
        empty_figure = go.Figure()
        empty_figure.update_layout(
            paper_bgcolor=CHART_THEME['bgcolor'],
            plot_bgcolor=CHART_THEME['bgcolor']
        )
        return (
            empty_figure, empty_figure, empty_figure, empty_figure, 
            empty_card, empty_card, empty_card, empty_card
        )

def create_monthly_chart(df):
    """Create monthly savings and investments comparison chart."""
    fig = go.Figure()
    
    # Add savings bars - now represents net savings (deposits minus withdrawals)
    fig.add_trace(go.Bar(
        name='Net Savings',
        x=df['Month'],
        y=df['Savings'],
        marker_color='rgb(46, 204, 113)'
    ))
    
    # Add withdrawal indicators as a separate series
    fig.add_trace(go.Bar(
        name='Withdrawals',
        x=df['Month'],
        y=df['Savings Withdrawals'],
        marker_color='rgb(231, 76, 60)',
        visible='legendonly'  # Hidden by default
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
    
    # Add Savings area - now using the net cumulative value that accounts for withdrawals
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
    
    # Add withdrawal markers - be more defensive with filtering
    withdrawal_df = df[df['Savings Withdrawals'] > 0]
    if not withdrawal_df.empty:
        fig.add_trace(go.Scatter(
            x=withdrawal_df['Month'],
            y=withdrawal_df['Cumulative Savings'],
            name='Withdrawals',
            mode='markers',
            marker=dict(
                symbol='triangle-down',
                size=10,
                color='rgb(231, 76, 60)',
                line=dict(width=1, color='white')
            ),
            hovertemplate="<b>Withdrawal</b>: %{customdata:,.0f} Kč<extra></extra>",
            customdata=withdrawal_df['Savings Withdrawals']
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
