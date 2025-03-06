from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from data_fetch import get_transactions
from get_categories import get_all_categories_api
from analysis import sum_values_by_criteria, sum_expenses_by_category, calculate_expense_ratio
from functools import lru_cache
from styles.theme import COLORS, TEXT_STYLES, CHART_THEME
from styles.common_styles import (
    CARD_STYLE, DROPDOWN_STYLE, CONTAINER_STYLE, 
    TABLE_STYLE, create_stat_card_style
)

def extract_day(date_str):
    """Extract day from date string in various formats."""
    try:
        if ('/' in date_str):
            # Handle "1/1/25" format
            return int(date_str.split('/')[0])
        elif ('.' in date_str):
            # Handle "1.1.2025" format
            return int(date_str.split('.')[0])
        return None
    except (ValueError, IndexError, AttributeError):
        return None

def create_stat_card(title, value="", color="income", id=None):
    """Create a styled metric card with optional ID."""
    card_style = create_stat_card_style(color)
    return dbc.Card([
        dbc.CardBody([
            html.H6(title, style=card_style['title']),
            html.H3(value, id=id, style=card_style['value'])
        ])
    ], style=CARD_STYLE, className="shadow-sm rounded-3")

def create_top_expenses_table(df):
    """Create styled top expenses table."""
    if df.empty:
        return html.Div("No expenses recorded", style={'color': COLORS['muted']})
    
    return dbc.Table([
        html.Thead(html.Tr([
            html.Th("Category"),
            html.Th("Amount", style={'textAlign': 'right'})
        ]), style={'backgroundColor': COLORS['surface']}),
        html.Tbody([
            html.Tr([
                html.Td(row['CATEGORY']),
                html.Td(f"{abs(row['VALUE_NUMERIC']):,.0f} Kč", 
                       style={'textAlign': 'right', 'color': COLORS['expenses']})
            ], style={'backgroundColor': COLORS['surface'] if i % 2 else COLORS['background']})
            for i, (_, row) in enumerate(df.iterrows())
        ])
    ], bordered=True, dark=True, hover=True)

layout = dbc.Container([
    # Month selector with fixed styling
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Monthly Overview", className="text-center",
                           style={'color': COLORS['text'], 'marginBottom': '20px'}),
                    dbc.Row([
                        dbc.Col(
                            html.Div([
                                dcc.Dropdown(
                                    id='month-selector',
                                    options=[{'label': m, 'value': m} for m in [
                                        'January', 'February', 'March', 'April', 'May', 'June',
                                        'July', 'August', 'September', 'October', 'November', 'December'
                                    ]],
                                    value='January',
                                    style=DROPDOWN_STYLE,
                                    className='dbc-dark'  # Updated className
                                )
                            ], style={'color': COLORS['text']})
                        , width=10),
                        dbc.Col(dbc.Button("Update", id="update-button", color="primary"), width=2)
                    ])
                ])
            ], style=CARD_STYLE, className="shadow-sm rounded-3")  # Added classes
        ])
    ], className="mb-4"),
    
    # Statistics cards
    dbc.Row([
        dbc.Col([
            create_stat_card(
                title="Income",
                color="income",
                id="income-value"
            )
        ], width=3),
        dbc.Col([
            create_stat_card(
                title="Expenses",
                color="expenses",
                id="expenses-value"
            )
        ], width=3),
        dbc.Col([
            create_stat_card(
                title="Net Income",
                color="savings",
                id="net-income-value"
            )
        ], width=3),
        dbc.Col([
            create_stat_card(
                title="Expense Ratio",
                color="expenses",
                id="expense-ratio-value"
            )
        ], width=3)
    ], className="mb-4"),
    
    # Charts
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Monthly Expenses", className="text-center mb-4",  # Changed from "Income vs Expenses"
                           style={'color': COLORS['text']}),
                    dcc.Graph(id='monthly-comparison')
                ])
            ], style=CARD_STYLE)
        ], md=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Expense Distribution", className="text-center mb-4",
                           style={'color': COLORS['text']}),
                    dcc.Graph(id='expense-distribution')
                ])
            ], style=CARD_STYLE)
        ], md=6)
    ], className="mb-4"),
    
    # Bottom row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Daily Expenses", className="text-center mb-4",
                           style={'color': COLORS['text']}),
                    dcc.Graph(id='daily-expenses')
                ])
            ], style=CARD_STYLE)
        ], md=8),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Top Expenses", className="text-center mb-4",
                           style={'color': COLORS['text']}),
                    html.Div(id='top-expenses')
                ])
            ], style=CARD_STYLE)
        ], md=4)
    ]),
    
    # Add custom CSS classes to the container
    html.Div([
        # ...existing monthly_layout content...
    ], style={
        '.dbc-dark .Select-control': {
            'backgroundColor': '#2d2d2d',
            'borderColor': '#404040'
        },
        '.dbc-dark .Select-menu-outer': {
            'backgroundColor': 'white'
        },
        '.dbc-dark .Select-value-label': {
            'color': 'white'
        },
        '.dbc-dark .Select--single > .Select-control .Select-value': {
            'color': 'white'
        },
        '.dbc-dark .VirtualizedSelectOption': {
            'backgroundColor': 'white',
            'color': 'black'
        },
        '.dbc-dark .VirtualizedSelectFocusedOption': {
            'backgroundColor': '#3498DB',
            'color': 'white'
        }
    })
], fluid=True, style={'backgroundColor': COLORS['background'], 'minHeight': '100vh'})

@callback(
    [Output('income-value', 'children'),
     Output('expenses-value', 'children'),
     Output('net-income-value', 'children'),
     Output('expense-ratio-value', 'children'),
     Output('monthly-comparison', 'figure'),
     Output('expense-distribution', 'figure'),
     Output('daily-expenses', 'figure'),
     Output('top-expenses', 'children')],
    [Input('month-selector', 'value')]
)
def update_dashboard(selected_month):
    """Update all dashboard components."""
    try:
        # Fetch and process data
        df = pd.DataFrame(get_transactions("Budget tracker 2025", "transactions"))
        df = df[df['TYPE'] != 'exclude']
        df['VALUE_NUMERIC'] = pd.to_numeric(df['VALUE'].str.replace('Kč', '').str.replace(',', ''))
        
        # Get monthly data
        month_data = df[df['MONTH'] == selected_month].copy()
        income_cats, expense_cats, saving_cats, investing_cats = get_all_categories_api("Budget tracker 2025")
        
        # Calculate metrics
        income = sum_values_by_criteria(month_data, 'VALUE', CATEGORY=income_cats)
        expenses = abs(sum_values_by_criteria(month_data, 'VALUE', CATEGORY=expense_cats))
        net_income = income - expenses
        expense_ratio = calculate_expense_ratio(month_data, income_cats, expense_cats)
        
        # Create comparison chart
        comparison_fig = create_comparison_chart(month_data, income_cats, expense_cats)
        
        # Create distribution chart
        distribution_fig = create_distribution_chart(month_data, expense_cats)
        
        # Create daily expenses chart
        daily_fig = create_daily_chart(month_data, expense_cats)
        
        # Create top expenses table
        top_expenses_df = month_data[
            (month_data['CATEGORY'].isin(expense_cats)) & 
            (month_data['VALUE_NUMERIC'] < 0)
        ].nsmallest(5, 'VALUE_NUMERIC')
        
        return (
            f"{income:,.0f} Kč",
            f"{expenses:,.0f} Kč",
            f"{net_income:,.0f} Kč",
            f"{expense_ratio:.1%}",
            comparison_fig,
            distribution_fig,
            daily_fig,
            create_top_expenses_table(top_expenses_df)
        )
    
    except Exception as e:
        print(f"Error updating dashboard: {e}")
        return "Error", "Error", "Error", "Error", {}, {}, {}, "Error loading data"

def create_comparison_chart(df, income_cats, expense_cats):
    """Create expenses bar chart."""
    expenses = df[df['CATEGORY'].isin(expense_cats)].groupby('CATEGORY')['VALUE_NUMERIC'].sum().abs()
    
    fig = go.Figure(data=[
        go.Bar(
            name='Expenses', 
            x=expenses.index, 
            y=expenses.values, 
            marker_color=COLORS['expenses']
        )
    ])
    
    fig.update_layout(
        barmode='group',
        paper_bgcolor=CHART_THEME['bgcolor'],
        plot_bgcolor=CHART_THEME['bgcolor'],
        height=CHART_THEME['height'],
        font={'color': COLORS['text']},
        showlegend=False,  # Removed legend since there's only one type of bar
        margin={'t': 30, 'b': 30, 'l': 30, 'r': 30},
        yaxis_title="Value (Kč)"
    )
    
    return fig

def create_distribution_chart(df, expense_cats):
    """Create expense distribution pie chart."""
    expenses = df[df['CATEGORY'].isin(expense_cats)].groupby('CATEGORY')['VALUE_NUMERIC'].sum().abs()
    
    fig = go.Figure(data=[go.Pie(
        labels=expenses.index,
        values=expenses.values,
        textposition='inside',
        textinfo='percent+label',
        marker={'colors': px.colors.qualitative.Set3},
        hovertemplate="<b>%{label}</b><br>Amount: %{value:,.0f} Kč<br>Percentage: %{percent}<extra></extra>"
    )])
    
    fig.update_layout(
        paper_bgcolor=CHART_THEME['bgcolor'],
        plot_bgcolor=CHART_THEME['bgcolor'],
        height=350,
        font={'color': COLORS['text']},
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.1,
            font=dict(size=12)
        ),
        margin=dict(t=30, b=30, l=30, r=120)  # Increased right margin for legend
    )
    
    return fig

def create_daily_chart(df, expense_cats):
    """Create daily expenses bar chart showing total expenses per day."""
    # Extract day using the existing extract_day function
    df['DAY'] = df['DATE'].apply(extract_day)
    
    # Filter for expenses and group by day
    daily_expenses = df[
        (df['CATEGORY'].isin(expense_cats)) & 
        (df['VALUE_NUMERIC'] < 0) &
        (df['DAY'].notna())
    ].groupby('DAY')['VALUE_NUMERIC'].sum().abs()
    
    if daily_expenses.empty:
        return go.Figure()
    
    # Sort by day
    daily_expenses = daily_expenses.reindex(index=sorted(daily_expenses.index))
    
    # Create bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=daily_expenses.index,
            y=daily_expenses.values,
            marker_color=COLORS['expenses'],
            hovertemplate="Day: %{x}<br>Total: %{y:,.0f} Kč<extra></extra>"
        )
    ])
    
    # Add moving average line
    fig.add_trace(go.Scatter(
        x=daily_expenses.index,
        y=daily_expenses.rolling(3, min_periods=1).mean(),
        mode='lines',
        line=dict(color=COLORS['primary'], width=2),
        name='3-day average',
        hovertemplate="Day: %{x}<br>3-day avg: %{y:,.0f} Kč<extra></extra>"
    ))
    
    fig.update_layout(
        paper_bgcolor=CHART_THEME['bgcolor'],
        plot_bgcolor=CHART_THEME['bgcolor'],
        height=400,
        font={'color': COLORS['text']},
        margin={'t': 30, 'b': 50, 'l': 50, 'r': 30},
        xaxis=dict(
            title="Day of Month",
            tickfont=dict(color=COLORS['text']),
            gridcolor='rgba(128,128,128,0.2)',
            dtick=1,
            type='category'
        ),
        yaxis=dict(
            title="Total Expenses (Kč)",
            tickfont=dict(color=COLORS['text']),
            gridcolor='rgba(128,128,128,0.2)'
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig
