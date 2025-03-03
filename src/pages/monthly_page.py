from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from data_fetch import get_transactions
from get_categories import get_all_categories_api
from analysis import sum_values_by_criteria, sum_expenses_by_category, calculate_expense_ratio
from functools import lru_cache

# Theme configuration
THEME = {
    'colors': {
        'income': '#2ECC71',     # Green
        'expenses': '#E74C3C',   # Red
        'savings': '#3498DB',    # Blue
        'investments': '#9B59B6', # Purple
        'background': '#2d2d2d',
        'surface': '#1a1a1a',
        'text': '#ffffff',
        'muted': '#adb5bd',
        'dropdown': {
            'background': '#1a1a1a',
            'text': '#ffffff',
            'selected': '#2d2d2d'
        }
    },
    'chart': {
        'bgcolor': 'rgba(0,0,0,0)',
        'gridcolor': 'rgba(255,255,255,0.1)',
        'height': 400
    }
}

# Update dropdown styles with better contrast and proper Dash dropdown syntax
DROPDOWN_STYLES = {
    'backgroundColor': THEME['colors']['dropdown']['background'],
    'color': '#000000',  # Black text
    'border': '1px solid #404040',
    'borderRadius': '4px',
    'option': {
        'color': '#000000',  # Black text for options
        'backgroundColor': THEME['colors']['dropdown']['background'],
    }
}

# Component styles
CARD_STYLE = {
    'backgroundColor': THEME['colors']['background'],
    'borderRadius': '10px',
    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
    'padding': '20px',
    'height': '100%'
}

# Layout components
def create_stat_card(title, value="", color="income", id=None):
    """Create a styled metric card with optional ID."""
    return dbc.Card([
        dbc.CardBody([
            html.H6(title, style={'color': THEME['colors']['muted'], 'fontSize': '0.9rem'}),
            html.H3(value, id=id, style={
                'color': THEME['colors'][color],
                'fontSize': '1.8rem',
                'fontWeight': 'bold'
            })
        ])
    ], style=CARD_STYLE)

def create_top_expenses_table(df):
    """Create styled top expenses table."""
    if df.empty:
        return html.Div("No expenses recorded", style={'color': THEME['colors']['muted']})
    
    return dbc.Table([
        html.Thead(html.Tr([
            html.Th("Category"),
            html.Th("Amount", style={'textAlign': 'right'})
        ]), style={'backgroundColor': THEME['colors']['surface']}),
        html.Tbody([
            html.Tr([
                html.Td(row['CATEGORY']),
                html.Td(f"{abs(row['VALUE_NUMERIC']):,.0f} Kč", 
                       style={'textAlign': 'right', 'color': THEME['colors']['expenses']})
            ], style={'backgroundColor': THEME['colors']['surface'] if i % 2 else THEME['colors']['background']})
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
                           style={'color': THEME['colors']['text'], 'marginBottom': '20px'}),
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
                                    style=DROPDOWN_STYLES,
                                    className='dash-dark-dropdown'
                                )
                            ], style={'color': THEME['colors']['text']})
                        , width=10),
                        dbc.Col(dbc.Button("Update", id="update-button", color="primary"), width=2)
                    ])
                ])
            ], style=CARD_STYLE)
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
                    html.H5("Income vs Expenses", className="text-center mb-4",
                           style={'color': THEME['colors']['text']}),
                    dcc.Graph(id='monthly-comparison')
                ])
            ], style=CARD_STYLE)
        ], md=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Expense Distribution", className="text-center mb-4",
                           style={'color': THEME['colors']['text']}),
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
                           style={'color': THEME['colors']['text']}),
                    dcc.Graph(id='daily-expenses')
                ])
            ], style=CARD_STYLE)
        ], md=8),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Top Expenses", className="text-center mb-4",
                           style={'color': THEME['colors']['text']}),
                    html.Div(id='top-expenses')
                ])
            ], style=CARD_STYLE)
        ], md=4)
    ])
], fluid=True)

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
    """Create income vs expenses comparison chart."""
    income = df[df['CATEGORY'].isin(income_cats)].groupby('CATEGORY')['VALUE_NUMERIC'].sum()
    expenses = df[df['CATEGORY'].isin(expense_cats)].groupby('CATEGORY')['VALUE_NUMERIC'].sum().abs()
    
    fig = go.Figure(data=[
        go.Bar(name='Income', x=income.index, y=income.values, marker_color=THEME['colors']['income']),
        go.Bar(name='Expenses', x=expenses.index, y=expenses.values, marker_color=THEME['colors']['expenses'])
    ])
    
    fig.update_layout(
        barmode='group',
        paper_bgcolor=THEME['chart']['bgcolor'],
        plot_bgcolor=THEME['chart']['bgcolor'],
        height=THEME['chart']['height'],
        font={'color': THEME['colors']['text']},
        legend={'orientation': 'h', 'y': 1.1},
        margin={'t': 30, 'b': 30, 'l': 30, 'r': 30}
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
        paper_bgcolor=THEME['chart']['bgcolor'],
        plot_bgcolor=THEME['chart']['bgcolor'],
        height=350,
        font={'color': THEME['colors']['text']},
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
    """Create daily expenses heatmap with improved date parsing."""
    def extract_day(date_str):
        try:
            if ('/' in date_str):
                # Handle "1/1/25" format
                day = int(date_str.split('/')[0])
            elif ('.' in date_str):
                # Handle "1.1.2025" format
                day = int(date_str.split('.')[0])
            else:
                return None
            return day
        except (ValueError, IndexError):
            return None

    # Extract day using custom function instead of datetime
    df['DAY'] = df['DATE'].apply(extract_day)
    
    # Filter out any rows where day extraction failed
    df = df[df['DAY'].notna()]
    
    daily_expenses = df[
        (df['CATEGORY'].isin(expense_cats)) & 
        (df['VALUE_NUMERIC'] < 0)
    ].groupby(['DAY', 'CATEGORY'])['VALUE_NUMERIC'].sum().abs()
    
    if daily_expenses.empty:
        return go.Figure()
    
    daily_matrix = daily_expenses.unstack(fill_value=0)
    
    # Sort the day index numerically
    daily_matrix = daily_matrix.reindex(index=sorted(daily_matrix.index))
    
    fig = go.Figure(data=go.Heatmap(
        z=daily_matrix.values,
        x=daily_matrix.columns,
        y=daily_matrix.index,
        colorscale='Viridis',
        hoverongaps=False,
        hovertemplate='Day: %{y}<br>Category: %{x}<br>Amount: %{z:,.0f} Kč<extra></extra>'
    ))
    
    fig.update_layout(
        paper_bgcolor=THEME['chart']['bgcolor'],
        plot_bgcolor=THEME['chart']['bgcolor'],
        height=600,  # Increased height
        font={'color': THEME['colors']['text']},
        margin={'t': 30, 'b': 80, 'l': 50, 'r': 30},  # Fixed margin syntax
        xaxis=dict(
            title="Category",
            tickfont=dict(color=THEME['colors']['text']),
            tickangle=45,
            side='bottom'
        ),
        yaxis=dict(
            title="Day of Month",
            tickfont=dict(color=THEME['colors']['text']),
            dtick=1,
            type='category',
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        )
    )
    
    return fig
