from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np
from data_fetch import get_transactions
from get_categories import get_all_categories_api
from analysis import sum_values_by_criteria

def create_stat_card(title, value, color="primary", is_percentage=False):
    """Create a statistics card with consistent styling."""
    return dbc.Card([
        dbc.CardBody([
            html.H6(title, className="text-muted mb-1"),
            html.H4(
                f"{value:,.2f}{'%' if is_percentage else ' Kč'}",
                className=f"text-{color}",
                style={'whiteSpace': 'nowrap'}
            )
        ], className="p-2")
    ], className="h-100")

layout = dbc.Container([
    html.H1("Savings & Investments Overview", className="my-4"),
    
    # Top row - All statistics cards
    dbc.Row([
        dbc.Col([html.Div(id="total-savings-card")], xs=12, sm=6, md=3, className="mb-3"),
        dbc.Col([html.Div(id="total-investments-card")], xs=12, sm=6, md=3, className="mb-3"),
        dbc.Col([html.Div(id="savings-ratio-card")], xs=12, sm=6, md=3, className="mb-3"),
        dbc.Col([html.Div(id="investment-ratio-card")], xs=12, sm=6, md=3, className="mb-3"),
    ], className="mb-4"),
    
    # Second row - Both charts side by side
    dbc.Row([
        # Left chart
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Monthly Savings & Investments", className="text-center mb-4"),
                    dbc.Spinner(
                        dcc.Graph(id='savings-chart', figure={})
                    )
                ])
            ])
        ], md=6),
        
        # Right chart
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Monthly Ratios (%)", className="text-center mb-4"),
                    dbc.Spinner(
                        dcc.Graph(id='ratio-chart', figure={})
                    )
                ])
            ])
        ], md=6)
    ])
], fluid=True)

@callback(
    [Output('savings-chart', 'figure'),
     Output('ratio-chart', 'figure'),
     Output('total-savings-card', 'children'),
     Output('total-investments-card', 'children'),
     Output('savings-ratio-card', 'children'),
     Output('investment-ratio-card', 'children')],
    [Input('overview-tabs', 'active_tab')]  # Changed from URL pathname to tab input
)
def update_savings_view(active_tab):
    """Update all components of the savings view."""
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
        
        # Create amounts chart
        fig1 = px.line(monthly_df, x='Month', y=['Savings', 'Investments'],
                      template='plotly_dark')
        
        # Create ratios chart
        fig2 = px.line(monthly_df, x='Month', y=['Savings Ratio', 'Investment Ratio'],
                      template='plotly_dark')
        
        # Update charts layout
        for fig in [fig1, fig2]:
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=450,  # Increased height
                margin={'t': 30, 'r': 30, 'b': 30, 'l': 30},
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(128,128,128,0.2)'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(128,128,128,0.2)',
                    tickformat=',.1f'
                )
            )
        
        # Add % symbol to ratio chart
        fig2.update_layout(
            yaxis_title="Percentage (%)"
        )
        
        return (
            fig1,
            fig2,
            create_stat_card("Total Savings", total_savings, "info"),
            create_stat_card("Total Investments", total_investments, "success"),
            create_stat_card("Savings Ratio", savings_ratio * 100, "info", is_percentage=True),
            create_stat_card("Investment Ratio", investment_ratio * 100, "success", is_percentage=True)
        )
        
    except Exception as e:
        print(f"Error updating savings view: {e}")
        empty_card = create_stat_card("Error", 0, "danger")
        return {}, {}, empty_card, empty_card, empty_card, empty_card
