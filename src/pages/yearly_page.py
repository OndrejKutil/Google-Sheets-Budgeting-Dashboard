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
from styles.theme import COLORS, CARD_STYLE, CHART_THEME, TEXT_STYLES

def create_stat_card(title, value, color='success'):
    """Simplified stat card without trend indicator."""
    return dbc.Card([
        dbc.CardBody([
            html.H5(title, className="text-muted mb-2", 
                   style={'fontSize': '0.9rem', 'fontWeight': '500'}),
            html.H3(
                f"{value:,.2f} Kč", 
                className=f"text-{color}",
                style={'fontSize': '1.8rem', 'fontWeight': '600'}
            )
        ])
    ], style=CARD_STYLE, className="shadow-sm rounded-3")

layout = dbc.Container([
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
            ], style={"height": "450px"})
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
            ], style={"height": "450px"})
        ], md=7)
    ], className="mb-4 g-3"),
    
    # Expenses Section
    html.H2("Expenses", className="mb-3"),
    
    dbc.Row([
        # Expense Trends
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Spinner(
                        dcc.Graph(
                            id='expense-trend-chart',
                            config={'displayModeBar': False}
                        )
                    )
                ])
            ], id="expense-trend-card", style={"height": "auto"})  # Changed to auto with ID for dynamic adjustment
        ], md=6),
        # Monthly Financial Summary (replaces Spending Heatmap)
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Spinner(
                        dcc.Graph(
                            id='monthly-summary-chart',
                            config={'displayModeBar': False}
                        )
                    )
                ])
            ], id="monthly-summary-card", style={"height": "auto"})
        ], md=6)
    ], className="mb-4 g-3"),
    
    # Income Section
    html.H2("Income", className="mb-3"),
    dbc.Row([
        # Monthly Income
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Spinner(
                        dcc.Graph(
                            id='monthly-income-chart',
                            config={'displayModeBar': False}
                        )
                    )
                ])
            ])
        ], md=6),
        # Income Distribution
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Spinner(
                        dcc.Graph(
                            id='income-distribution-chart',
                            config={'displayModeBar': False}
                        )
                    )
                ])
            ])
        ], md=6)
    ], className="mb-4"),
    
    # Update button
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
], fluid=True, style={'backgroundColor': COLORS['background']})

@callback(
    [Output('yearly-stats', 'children'),
     Output('yearly-category-chart', 'figure'),
     Output('expense-trend-chart', 'figure'),
     Output('monthly-summary-chart', 'figure'),  # Changed from spending-heatmap
     Output('monthly-income-chart', 'figure'),
     Output('income-distribution-chart', 'figure'),
     Output('expense-trend-card', 'style'),
     Output('monthly-summary-card', 'style')],  # Changed from spending-heatmap-card
    [Input('overview-tabs', 'active_tab'),
     Input('update-yearly-button', 'n_clicks')]
)
def update_yearly_view(active_tab, n_clicks):
    """Update all dashboard components."""
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
        
        # Use standard chart height from theme for all charts
        standard_height = CHART_THEME['height']
        
        # Create consistent card style with standard height
        standard_card_style = {"height": "auto"}  # Let height be determined by content
        
        return (
            yearly_stats,
            create_category_pie(df, expense_cats),
            create_expense_trend(df, expense_cats, standard_height),
            create_monthly_summary_chart(df, income_cats, expense_cats, saving_cats, investing_cats, standard_height),
            create_monthly_income(df, income_cats),
            create_income_distribution(df, income_cats),
            standard_card_style,
            standard_card_style
        )
    except Exception as e:
        print(f"Error updating yearly view: {e}")
        default_style = {"height": "auto"}
        return no_data_message(), {}, {}, {}, {}, {}, default_style, default_style

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
    
    # Calculate profit (income - expenses - investments)
    profit = total_income - total_expenses - total_investments
    
    # Calculate net cashflow (income - expenses - investments - savings)
    net_cashflow = total_income - total_expenses - total_investments - total_savings
    
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
            dbc.Col(create_stat_card("Profit", profit, 
                                   "success" if profit >= 0 else "danger"), md=6),
            dbc.Col(create_stat_card("Net Cashflow", net_cashflow, 
                                   "success" if net_cashflow >= 0 else "danger"), md=6)
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

def create_monthly_summary_chart(df, income_cats, expense_cats, saving_cats, investing_cats, height=None):
    """Create bar chart showing monthly financial summary."""
    monthly_data = []
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    
    for month in months:
        income = sum_values_by_criteria(df, 'VALUE', CATEGORY=income_cats, MONTH=month)
        expenses = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=expense_cats, MONTH=month))
        investments = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=investing_cats, MONTH=month))
        savings = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=saving_cats, MONTH=month))
        
        profit = income - expenses - investments
        cashflow = income - expenses - investments - savings
        
        monthly_data.append({
            'Month': month,
            'Income': income,
            'Expenses': expenses,
            'Profit': profit,
            'Cashflow': cashflow
        })
    
    summary_df = pd.DataFrame(monthly_data)
    
    fig = go.Figure()
    
    # Add bars for each metric
    fig.add_trace(go.Bar(
        x=summary_df['Month'],
        y=summary_df['Income'],
        name='Income',
        marker_color=COLORS['income'],
        hovertemplate='%{x}<br>Income: %{y:,.0f} Kč<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        x=summary_df['Month'],
        y=summary_df['Expenses'],
        name='Expenses',
        marker_color=COLORS['expenses'],
        hovertemplate='%{x}<br>Expenses: %{y:,.0f} Kč<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        x=summary_df['Month'],
        y=summary_df['Profit'],
        name='Profit',
        marker_color=COLORS['purple'],  # Using purple color for profit
        hovertemplate='%{x}<br>Profit: %{y:,.0f} Kč<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        x=summary_df['Month'],
        y=summary_df['Cashflow'],
        name='Cashflow',
        marker_color=COLORS['info'],  # Using info color for cashflow
        hovertemplate='%{x}<br>Cashflow: %{y:,.0f} Kč<extra></extra>'
    ))
    
    # Use significantly increased height
    if height is None:
        height = CHART_THEME['height'] + 175  # Increased to add significant more height
    
    fig.update_layout(
        title='Monthly Financial Summary',
        barmode='group',
        paper_bgcolor=CHART_THEME['paper_bgcolor'],
        plot_bgcolor=CHART_THEME['bgcolor'],
        title_x=0.5,
        title_font_size=CHART_THEME['title_font_size'],
        title_font_color=CHART_THEME['font_color'],
        height=height,
        xaxis=dict(
            title='Month',
            title_font=dict(color=CHART_THEME['font_color']),  # Explicitly setting title font color to white
            tickangle=45,
            showgrid=True,
            gridcolor=CHART_THEME['grid_color'],
            tickfont=dict(color=CHART_THEME['font_color'])
        ),
        yaxis=dict(
            title='Amount (Kč)',
            title_font=dict(color=CHART_THEME['font_color']),  # Explicitly setting title font color to white
            showgrid=True,
            gridcolor=CHART_THEME['grid_color'],
            tickfont=dict(color=CHART_THEME['font_color']),
            tickformat=',.0f',
            dtick=5000  # Changed from 2500 to 5000 for less frequent ticks
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=CHART_THEME['font_color'])
        )
    )
    
    return fig

def create_expense_trend(df, expense_cats, height=None):
    """Create line chart showing expense trends."""
    monthly_expenses = {}
    for month in ['January', 'February', 'March', 'April', 'May', 'June', 
                  'July', 'August', 'September', 'October', 'November', 'December']:
        expenses = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=expense_cats, MONTH=month))
        monthly_expenses[month] = expenses if expenses != 0 else None
    
    trend_df = pd.DataFrame({
        'Month': list(monthly_expenses.keys()),
        'Expenses': list(monthly_expenses.values())
    })
    
    fig = px.line(trend_df, x='Month', y='Expenses',
                  title='Expense Trends',
                  template='plotly_dark')
    
    fig.update_traces(
        line=dict(color=COLORS['expenses'], width=3),
        mode='lines+markers'
    )
    
    # Use significantly increased height for this chart
    if height is None:
        height = CHART_THEME['height'] + 175  # Increased to add significant more height
    
    fig.update_layout(
        paper_bgcolor=CHART_THEME['paper_bgcolor'],
        plot_bgcolor=CHART_THEME['bgcolor'],
        title_x=0.5,
        title_font_size=CHART_THEME['title_font_size'],
        title_font_color=CHART_THEME['font_color'],
        showlegend=False,
        height=height,
        xaxis=dict(
            title='Month',
            title_font=dict(color=CHART_THEME['font_color']),
            tickangle=45,
            showgrid=True,
            gridcolor=CHART_THEME['grid_color'],
            tickfont=dict(color=CHART_THEME['font_color'])
        ),
        yaxis=dict(
            title='Amount (Kč)',
            title_font=dict(color=CHART_THEME['font_color']),
            showgrid=True,
            gridcolor=CHART_THEME['grid_color'],
            tickfont=dict(color=CHART_THEME['font_color']),
            tickformat=',.0f',
            dtick=2500  # Keeping finer tick spacing (2500) for expense trends
        )
    )
    return fig

def create_monthly_income(df, income_cats):
    """Create stacked bar chart showing income sources by month."""
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    
    # Create a list to store monthly data
    monthly_data = []
    
    for month in months:
        month_df = df[df['MONTH'] == month]
        month_dict = {'Month': month}
        
        for category in income_cats:
            amount = sum_values_by_criteria(month_df, 'VALUE', CATEGORY=[category])
            if amount > 0:  # Only include positive income
                month_dict[category] = amount
            else:
                month_dict[category] = 0
                
        monthly_data.append(month_dict)
    
    # Convert to DataFrame
    income_df = pd.DataFrame(monthly_data)
    
    # Create stacked bar chart
    fig = go.Figure()
    
    # Add bar traces for each income category
    for category in income_cats:
        if category in income_df.columns:  # Only add if category has data
            fig.add_trace(go.Bar(
                name=category,
                x=income_df['Month'],
                y=income_df[category],
                hovertemplate="%{x}<br>" +
                             f"{category}: %{{y:,.0f}} Kč<br>" +
                             "<extra></extra>"
            ))
    
    fig.update_layout(
        title={
            'text': 'Monthly Income by Source',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        barmode='stack',
        paper_bgcolor=CHART_THEME['paper_bgcolor'],
        plot_bgcolor=CHART_THEME['bgcolor'],
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
        height=CHART_THEME['height'],
        xaxis=dict(
            title="Month",
            title_font=dict(color=CHART_THEME['font_color']),
            tickangle=45,
            showgrid=True,
            gridcolor=CHART_THEME['grid_color'],
            tickfont=dict(color=CHART_THEME['font_color'])
        ),
        yaxis=dict(
            title='Amount (Kč)',
            title_font=dict(color=CHART_THEME['font_color']),
            showgrid=True,
            gridcolor=CHART_THEME['grid_color'],
            tickfont=dict(color=CHART_THEME['font_color']),
            tickformat=',.0f'
        )
    )
    
    return fig

def create_income_distribution(df, income_cats):
    """Create income trend comparison chart."""
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    
    # Calculate total income for each month
    monthly_totals = []
    running_total = 0
    
    for month in months:
        month_df = df[df['MONTH'] == month]
        month_income = sum_values_by_criteria(month_df, 'VALUE', CATEGORY=income_cats)
        running_total += month_income
        
        monthly_totals.append({
            'Month': month,
            'Monthly Income': month_income,
            'Cumulative Income': running_total
        })
    
    # Convert to DataFrame
    income_df = pd.DataFrame(monthly_totals)
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add monthly income bars
    fig.add_trace(
        go.Bar(
            name='Monthly Income',
            x=income_df['Month'],
            y=income_df['Monthly Income'],
            marker_color=COLORS['income']
        ),
        secondary_y=False
    )
    
    # Add cumulative line
    fig.add_trace(
        go.Scatter(
            name='Cumulative Income',
            x=income_df['Month'],
            y=income_df['Cumulative Income'],
            line=dict(color=COLORS['savings'], width=3),
            mode='lines+markers'
        ),
        secondary_y=True
    )
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Income Progress',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        paper_bgcolor=CHART_THEME['paper_bgcolor'],
        plot_bgcolor=CHART_THEME['bgcolor'],
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
        height=CHART_THEME['height'],
        xaxis=dict(
            title="Month",
            title_font=dict(color=CHART_THEME['font_color']),
            tickangle=45,
            showgrid=True,
            gridcolor=CHART_THEME['grid_color'],
            tickfont=dict(color=CHART_THEME['font_color'])
        )
    )
    
    # Update yaxis properties
    fig.update_yaxes(
        title_text="Monthly Income (Kč)",
        title_font=dict(color=CHART_THEME['font_color']),
        showgrid=True,
        gridcolor=CHART_THEME['grid_color'],
        tickfont=dict(color=CHART_THEME['font_color']),
        tickformat=',.0f',
        secondary_y=False
    )
    fig.update_yaxes(
        title_text="Cumulative Income (Kč)",
        title_font=dict(color=CHART_THEME['font_color']),
        showgrid=False,
        tickfont=dict(color=CHART_THEME['font_color']),
        tickformat=',.0f',
        secondary_y=True
    )
    
    return fig
