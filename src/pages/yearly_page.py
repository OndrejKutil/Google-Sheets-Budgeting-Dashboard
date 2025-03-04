import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from data_fetch import get_transactions
from get_categories import get_all_categories_api
from analysis import sum_values_by_criteria, sum_expenses_by_category

CHART_THEME = {
    'bgcolor': 'rgba(0,0,0,0)',
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'font_color': 'white',
    'grid_color': 'rgba(128,128,128,0.2)',
    'title_font_size': 20,
    'height': 400,
}

COLORS = {
    'income': '#2ECC71',
    'expenses': '#E74C3C',
    'savings': '#3498DB',
    'investments': '#9B59B6',
    'success': 'text-success',
    'danger': 'text-danger',
    'info': 'text-info',
    'primary': 'text-primary'
}

def create_stat_card(title, value, color='success'):
    """Simplified stat card without trend indicator."""
    return dbc.Card([
        dbc.CardBody([
            html.H5(title, className="text-muted mb-2"),
            html.H3(
                f"{value:,.2f} Kč", 
                className=f"text-{color}"
            )
        ])
    ], className="shadow-sm h-100 rounded-3")

layout = dbc.Container([
    html.H1("Yearly Overview", className="my-4"),
    
    # Top row - Stats and Category Distribution
    dbc.Row([
        # Stats Card
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Div(id="yearly-stats")
                        ], className="p-3")
                    ])
                ])
            ], style={"height": "450px"})  # Fixed height
        ], md=5),
        
        # Category Distribution
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Expense Distribution", className="text-center mb-4"),
                    dbc.Spinner(
                        dcc.Graph(
                            id='yearly-category-chart',
                            config={'displayModeBar': False}
                        )
                    )
                ])
            ], style={"height": "450px"})  # Fixed height
        ], md=7)
    ], className="mb-4 g-3"),
    
    # Middle row - Bar Chart
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Monthly Income vs Expenses", className="text-center mb-4"),
                    dbc.Spinner(
                        dcc.Graph(
                            id='monthly-comparison-chart',
                            config={'displayModeBar': False}
                        )
                    )
                ])
            ], className="shadow rounded-3")
        ])
    ], className="mb-4"),
    
    # Bottom row - Trends and Heatmap
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Financial Trends", className="text-center mb-4"),
                    dbc.Spinner(
                        dcc.Graph(
                            id='yearly-trend-chart',
                            config={'displayModeBar': False}
                        )
                    )
                ])
            ], className="shadow rounded-3")
        ], md=8),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Spending Heatmap", className="text-center mb-4"),
                    dbc.Spinner(
                        dcc.Graph(
                            id='spending-heatmap',
                            config={'displayModeBar': False}
                        )
                    )
                ])
            ], className="shadow rounded-3")
        ], md=4)
    ], className="mb-4 g-3"),
    
    # Update button with improved styling
    dbc.Row([
        dbc.Col([
            dbc.Button(
                "Update Dashboard",
                id="update-yearly-button",
                color="primary",
                className="w-100 rounded-3 shadow-sm"
            )
        ], md={"size": 4, "offset": 4})
    ])
], fluid=True, className="px-4")

@callback(
    [Output('yearly-stats', 'children'),
     Output('yearly-trend-chart', 'figure'),
     Output('yearly-category-chart', 'figure'),
     Output('monthly-comparison-chart', 'figure'),
     Output('spending-heatmap', 'figure')],
    [Input('overview-tabs', 'active_tab'),
     Input('update-yearly-button', 'n_clicks')]
)
def update_yearly_view(active_tab, n_clicks):
    """Update all dashboard components."""
    # Remove the pathname check and always update when tab is active
    try:
        SPREADSHEET_NAME = "Budget tracker 2025"
        df = pd.DataFrame(get_transactions(SPREADSHEET_NAME, "transactions"))
        # Filter out excluded transactions
        df = df[df['TYPE'] != 'exclude']
        income_cats, expense_cats, saving_cats, investing_cats = get_all_categories_api(SPREADSHEET_NAME)
        
        # Clean and convert values to numeric
        df['VALUE_NUMERIC'] = df['VALUE'].str.replace('Kč', '').str.replace(',', '').astype(float)
        
        # Create improved yearly statistics card
        yearly_stats = create_yearly_stats(df, income_cats, expense_cats, saving_cats, investing_cats)
        
        # Create enhanced trend chart
        trend_fig = create_trend_chart(df, income_cats, expense_cats, saving_cats, investing_cats)
        
        # Create improved pie chart
        pie_fig = create_category_pie(df, expense_cats)
        
        # Create new bar chart
        bar_fig = create_monthly_comparison(df, income_cats, expense_cats)
        
        # Create new heatmap
        heatmap_fig = create_spending_heatmap(df, expense_cats)
        
        return yearly_stats, trend_fig, pie_fig, bar_fig, heatmap_fig
    
    except Exception as e:
        print(f"Error updating yearly view: {e}")
        return no_data_message(), {}, {}, {}, {}

def no_data_message():
    return html.Div("No data available", className="text-muted text-center")

def empty_chart(message="No data available"):
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

def create_yearly_stats(df, income_cats, expense_cats, saving_cats, investing_cats):
    """Create statistics cards without trends."""
    # Calculate yearly totals
    total_income = sum_values_by_criteria(df, 'VALUE', CATEGORY=income_cats)
    total_expenses = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=expense_cats))
    total_savings = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=saving_cats))
    total_investments = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=investing_cats))
    net_cashflow = total_income - total_expenses
    
    return html.Div([
        dbc.Row([
            dbc.Col(create_stat_card("Total Income", total_income, "success"), md=6),
            dbc.Col(create_stat_card("Total Expenses", abs(total_expenses), "danger"), md=6)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col(create_stat_card("Total Savings", total_savings, "info"), md=6),
            dbc.Col(create_stat_card("Total Investments", total_investments, "primary"), md=6)
        ], className="mb-3"),
        html.Hr(),
        dbc.Row([
            dbc.Col(create_stat_card("Net Cashflow", net_cashflow, 
                                   "success" if net_cashflow >= 0 else "danger"))
        ])
    ])

def create_trend_chart(df, income_cats, expense_cats, saving_cats, investing_cats):
    """Create enhanced trend chart with improved styling."""
    all_months = ['January', 'February', 'March', 'April', 'May', 'June', 
                 'July', 'August', 'September', 'October', 'November', 'December']
    monthly_data = []
    
    for month in all_months:
        # Get all transactions for this month
        month_df = df[df['MONTH'] == month]
        
        # Only process months that have any transactions
        if len(month_df) > 0:
            month_income = sum_values_by_criteria(df, 'VALUE', CATEGORY=income_cats, MONTH=month)
            month_expenses = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=expense_cats, MONTH=month))
            month_savings = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=saving_cats, MONTH=month))
            month_investments = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=investing_cats, MONTH=month))
            
            monthly_data.append({
                'Month': month,
                'Income': month_income if month_income != 0 else 0,
                'Expenses': month_expenses if month_expenses != 0 else 0,
                'Savings': month_savings if month_savings != 0 else 0,
                'Investments': month_investments if month_investments != 0 else 0
            })
        else:
            # For months with no data, set all values to None
            monthly_data.append({
                'Month': month,
                'Income': None,
                'Expenses': None,
                'Savings': None,
                'Investments': None
            })
    
    trend_df = pd.DataFrame(monthly_data)
    fig = px.line(trend_df, x='Month', 
                       y=['Income', 'Expenses', 'Savings', 'Investments'],
                       title='Monthly Financial Trends',
                       labels={'value': 'Amount (Kč)', 'variable': 'Type'},
                       template='plotly_dark')  # Changed to dark theme
    
    # Customize trend chart
    fig.update_layout(
        paper_bgcolor=CHART_THEME['paper_bgcolor'],
        plot_bgcolor=CHART_THEME['bgcolor'],
        title_x=0.5,
        title_font_size=CHART_THEME['title_font_size'],
        title_font_color=CHART_THEME['font_color'],
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=CHART_THEME['font_color'])
        ),
        xaxis=dict(
            tickangle=45,
            showgrid=True,
            gridwidth=1,
            gridcolor=CHART_THEME['grid_color'],
            color=CHART_THEME['font_color'],
            tickfont=dict(color=CHART_THEME['font_color'])
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor=CHART_THEME['grid_color'],
            color=CHART_THEME['font_color'],
            tickformat=',.0f',
            tickfont=dict(color=CHART_THEME['font_color'])
        ),
        height=CHART_THEME['height']
    )
    
    # Update line colors and style
    fig.update_traces(
        selector=dict(name='Income'),
        line=dict(color=COLORS['income'], width=3),
        mode='lines+markers'
    )
    fig.update_traces(
        selector=dict(name='Expenses'),
        line=dict(color=COLORS['expenses'], width=3),
        mode='lines+markers'
    )
    fig.update_traces(
        selector=dict(name='Savings'),
        line=dict(color=COLORS['savings'], width=3),
        mode='lines+markers'
    )
    fig.update_traces(
        selector=dict(name='Investments'),
        line=dict(color=COLORS['investments'], width=3),  # Purple color for investments
        mode='lines+markers'
    )
    
    return fig

def create_category_pie(df, expense_cats):
    """Create enhanced pie chart with side legend."""
    expenses_by_category = sum_expenses_by_category(df, expense_cats)
    if expenses_by_category:
        category_data = pd.DataFrame({
            'Category': list(expenses_by_category.keys()),
            'Amount': list(expenses_by_category.values())
        })
        
        fig = px.pie(
            category_data,
            values='Amount',
            names='Category',
            title='Yearly Expense Distribution',
            template='plotly_dark',  # Changed to dark theme
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_layout(
            paper_bgcolor=CHART_THEME['paper_bgcolor'],
            plot_bgcolor=CHART_THEME['bgcolor'],
            title_x=0.5,
            title_font_size=CHART_THEME['title_font_size'],
            title_font_color=CHART_THEME['font_color'],
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=0.85,  # Position legend to the right of pie chart
                font=dict(
                    color=CHART_THEME['font_color'],
                    size=12
                )
            ),
            height=CHART_THEME['height'],
            margin=dict(r=150, l=0, t=30, b=30)  # Adjust margins to center pie chart
        )
    else:
        fig = empty_chart("No expenses recorded")

    return fig

def create_monthly_comparison(df, income_cats, expense_cats):
    """Create new bar chart comparing monthly income and expenses."""
    all_months = ['January', 'February', 'March', 'April', 'May', 'June', 
                 'July', 'August', 'September', 'October', 'November', 'December']
    monthly_data = []
    
    for month in all_months:
        # Get all transactions for this month
        month_df = df[df['MONTH'] == month]
        
        # Only process months that have any transactions
        if len(month_df) > 0:
            month_income = sum_values_by_criteria(df, 'VALUE', CATEGORY=income_cats, MONTH=month)
            month_expenses = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=expense_cats, MONTH=month))
            
            monthly_data.append({
                'Month': month,
                'Income': month_income if month_income != 0 else 0,
                'Expenses': month_expenses if month_expenses != 0 else 0
            })
        else:
            # For months with no data, set all values to None
            monthly_data.append({
                'Month': month,
                'Income': None,
                'Expenses': None
            })
    
    comparison_df = pd.DataFrame(monthly_data)
    fig = px.bar(comparison_df, x='Month', y=['Income', 'Expenses'],
                 title='Monthly Income vs Expenses',
                 labels={'value': 'Amount (Kč)', 'variable': 'Type'},
                 template='plotly_dark',
                 barmode='group')
    
    fig.update_layout(
        paper_bgcolor=CHART_THEME['paper_bgcolor'],
        plot_bgcolor=CHART_THEME['bgcolor'],
        title_x=0.5,
        title_font_size=CHART_THEME['title_font_size'],
        title_font_color=CHART_THEME['font_color'],
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=CHART_THEME['font_color'])
        ),
        xaxis=dict(
            tickangle=45,
            showgrid=True,
            gridwidth=1,
            gridcolor=CHART_THEME['grid_color'],
            color=CHART_THEME['font_color'],
            tickfont=dict(color=CHART_THEME['font_color'])
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor=CHART_THEME['grid_color'],
            color=CHART_THEME['font_color'],
            tickformat=',.0f',
            tickfont=dict(color=CHART_THEME['font_color'])
        ),
        height=CHART_THEME['height']
    )
    
    return fig

def create_spending_heatmap(df, expense_cats):
    """Create heatmap with improved text visibility and absolute values."""
    # Create proper copy of filtered data
    heatmap_data = df[df['CATEGORY'].isin(expense_cats)].copy()
    
    # Convert values to absolute values
    heatmap_data.loc[:, 'VALUE_NUMERIC'] = heatmap_data['VALUE_NUMERIC'].abs()
    
    # Define months in chronological order
    month_order = [
        'January', 'February', 'March', 'April', 'May', 'June', 
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    
    # Create categorical month column with explicit order
    heatmap_data.loc[:, 'MONTH'] = pd.Categorical(
        heatmap_data['MONTH'],
        categories=month_order,
        ordered=True
    )
    
    # Create pivot table with reordered months
    pivot_table = pd.pivot_table(
        heatmap_data,
        index='CATEGORY',
        columns='MONTH',
        values='VALUE_NUMERIC',
        aggfunc='sum',
        fill_value=0,
        observed=True
    )
    
    # Reorder columns to ensure chronological order
    pivot_table = pivot_table.reindex(columns=month_order)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale='Viridis',
        hoverongaps=False,
        hovertemplate='Category: %{y}<br>Month: %{x}<br>Amount: %{z:,.0f} Kč<extra></extra>'
    ))
    
    fig.update_layout(
        title='Monthly Spending by Category',
        xaxis_nticks=12,
        paper_bgcolor=CHART_THEME['paper_bgcolor'],
        plot_bgcolor=CHART_THEME['bgcolor'],
        title_x=0.5,
        title_font_size=CHART_THEME['title_font_size'],
        title_font_color=CHART_THEME['font_color'],
        height=CHART_THEME['height'],
        # Improve text visibility
        xaxis=dict(
            tickfont=dict(color='white', size=12),
            title_font=dict(color='white', size=14)
        ),
        yaxis=dict(
            tickfont=dict(color='white', size=12),
            title_font=dict(color='white', size=14)
        )
    )
    
    return fig
