import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output
import plotly.express as px
import pandas as pd
from data_fetch import get_transactions
from get_categories import get_all_categories_api
from analysis import sum_values_by_criteria, sum_expenses_by_category, calculate_expense_ratio

"""Monthly overview page showing detailed statistics for a selected month."""

layout = dbc.Container([
    html.H1("Monthly Overview", className="my-4"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Month Selection", className="text-center mb-3"),
                    dcc.Dropdown(
                        id='month-selector',
                        options=[
                            {'label': month, 'value': month} for month in [
                                'January', 'February', 'March', 'April', 'May', 'June',
                                'July', 'August', 'September', 'October', 'November', 'December'
                            ]
                        ],
                        value='January',
                        clearable=False,
                        className="mb-3",
                        style={'color': '#000', 'backgroundColor': '#FFF'}
                    ),
                    dbc.Button(
                        "Update Overview",
                        id="update-monthly-button",
                        color="primary",
                        className="w-100"
                    )
                ])
            ], className="mb-4")
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Monthly Statistics", className="text-center mb-4"),
                    dbc.Spinner(html.Div(id="monthly-stats")),
                ])
            ], className="h-100")
        ], md=5),  # Changed from md=4 to md=5
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Category Breakdown", className="text-center mb-4"),
                    dbc.Spinner(
                        dcc.Graph(id='monthly-category-chart', figure={})
                    )
                ])
            ], className="h-100")
        ], md=7)  # Changed from md=8 to md=7
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Top Expenses", className="text-center mb-4"),
                    dbc.Spinner(html.Div(id="monthly-top-expenses")),
                ])
            ], className="mt-4")
        ])
    ])
])

def empty_chart(message="No data available") -> dict:
    """Create an empty chart placeholder with custom message.

    Args:
        message: Text to display in empty chart area

    Returns:
        dict: Plotly figure with centered message
    """
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

def no_data_message() -> html.Div:
    """Create a standardized no-data message component."""
    return html.Div("No data available", className="text-muted text-center")

@callback(
    [Output('monthly-stats', 'children'),
     Output('monthly-category-chart', 'figure'),
     Output('monthly-top-expenses', 'children')],
    [Input('month-selector', 'value'),
     Input('update-monthly-button', 'n_clicks')]
)
def update_monthly_view(selected_month: str, n_clicks: int) -> tuple:
    """Update all components of the monthly view based on selected month.
    
    Creates three main components:
    1. Statistics panel showing income, expenses, savings and ratios
    2. Pie chart showing expense distribution by category
    3. Table showing top 5 expenses for the month

    Args:
        selected_month: Name of selected month
        n_clicks: Button click counter (not used directly)

    Returns:
        tuple: (stats_component, pie_chart, expenses_table)
    """
    if not selected_month:
        return no_data_message(), {}, no_data_message()
    
    try:
        SPREADSHEET_NAME = "Budget tracker 2025"
        df = pd.DataFrame(get_transactions(SPREADSHEET_NAME, "transactions"))
        # Filter out excluded transactions
        df = df[df['TYPE'] != 'exclude']
        income_cats, expense_cats, saving_cats, investing_cats = get_all_categories_api(SPREADSHEET_NAME)
        
        # Calculate monthly statistics
        month_income = sum_values_by_criteria(df, 'VALUE', CATEGORY=income_cats, MONTH=selected_month)
        month_expenses = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=expense_cats, MONTH=selected_month))
        month_savings = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=saving_cats, MONTH=selected_month))
        month_investments = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=investing_cats, MONTH=selected_month))
        net_income = month_income - month_expenses
        expense_ratio = calculate_expense_ratio(df, income_cats, expense_cats, month=selected_month)
        
        # Create statistics display
        stats = html.Div([
            dbc.Row([
                dbc.Col([
                    html.H5("Income:", className="text-muted mb-0"),
                    html.H3(f"{month_income:,.2f} Kč", 
                           className="text-success",
                           style={'whiteSpace': 'nowrap'})  # Add nowrap
                ], className="text-center mb-3"),
                dbc.Col([
                    html.H5("Expenses:", className="text-muted mb-0"),
                    html.H3(f"{month_expenses:,.2f} Kč", 
                           className="text-danger",
                           style={'whiteSpace': 'nowrap'})  # Add nowrap
                ], className="text-center mb-3")
            ]),
            dbc.Row([
                dbc.Col([
                    html.H5("Savings:", className="text-muted mb-0"),
                    html.H3(f"{month_savings:,.2f} Kč", 
                           className="text-info",
                           style={'whiteSpace': 'nowrap'})  # Add nowrap
                ], className="text-center mb-3"),
                dbc.Col([
                    html.H5("Investments:", className="text-muted mb-0"),
                    html.H3(f"{month_investments:,.2f} Kč", 
                           className="text-primary",
                           style={'whiteSpace': 'nowrap'})  # Add nowrap
                ], className="text-center mb-3")
            ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.H5("Net Income:", className="text-muted mb-0"),
                    html.H2(
                        f"{net_income:,.2f} Kč",
                        className=f"{'text-success' if net_income >= 0 else 'text-danger'}"
                    )
                ], className="text-center mb-2"),
                dbc.Col([
                    html.H5("Expense Ratio:", className="text-muted mb-0"),
                    html.H2(
                        f"{expense_ratio:.1%}",
                        className=f"{'text-success' if expense_ratio < 0.8 else 'text-warning' if expense_ratio < 1 else 'text-danger'}"
                    )
                ], className="text-center")
            ])
        ])
        
        # Create category breakdown chart
        expenses_by_category = sum_expenses_by_category(df, expense_cats, month=selected_month)
        if expenses_by_category:
            category_data = pd.DataFrame({
                'Category': list(expenses_by_category.keys()),
                'Amount': list(expenses_by_category.values())
            })
            
            category_fig = px.pie(
                category_data,
                values='Amount',
                names='Category',
                title=f"Expense Categories - {selected_month}",
                template='plotly_dark',  # Changed to dark theme
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            category_fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title_x=0.5,
                title_font_size=20,
                title_font_color='white',
                showlegend=True,
                legend=dict(
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05,
                    orientation="v",
                    font=dict(color='white')
                ),
                height=400,
                margin=dict(r=150)
            )
        else:
            category_fig = empty_chart("No expenses for this month")
        
        # Create top expenses table
        df_month = df[df['MONTH'] == selected_month].copy()
        df_month['VALUE_NUMERIC'] = df_month['VALUE'].str.replace('Kč', '').str.replace(',', '').astype(float)
        top_expenses = df_month[df_month['VALUE_NUMERIC'] < 0].nsmallest(5, 'VALUE_NUMERIC')
        
        top_expenses_table = dbc.Table([
            html.Thead(html.Tr([
                html.Th("Category"), html.Th("Description"), html.Th("Amount", className="text-end")
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(row['CATEGORY']),
                    html.Td(row['DESCRIPTION']),
                    html.Td(f"{abs(row['VALUE_NUMERIC']):,.2f} Kč", className="text-end text-danger")
                ]) for _, row in top_expenses.iterrows()
            ])
        ], bordered=True, hover=True, responsive=True, className="mt-3")
        
        return stats, category_fig, top_expenses_table
    except Exception as e:
        print(f"Error updating monthly view: {e}")
        return no_data_message(), {}, no_data_message()
