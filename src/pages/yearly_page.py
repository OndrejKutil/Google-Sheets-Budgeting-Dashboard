import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output
import plotly.express as px
import pandas as pd
from data_fetch import get_transactions
from get_categories import get_all_categories_api
from analysis import sum_values_by_criteria, sum_expenses_by_category

layout = dbc.Container([
    html.H1("Yearly Overview", className="my-4"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Annual Statistics", className="card-title text-center mb-4"),
                    dbc.Spinner(html.Div(id="yearly-stats")),
                ])
            ], className="h-100")
        ], md=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Monthly Trends", className="card-title text-center mb-4"),
                    dbc.Spinner(
                        dcc.Graph(id='yearly-trend-chart', figure={})
                    )
                ])
            ], className="h-100")
        ], md=6)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Category Distribution", className="card-title text-center mb-4"),
                    dbc.Spinner(
                        dcc.Graph(id='yearly-category-chart', figure={})
                    ),
                    html.Div(
                        dbc.Button(
                            "Update Charts",
                            id="update-yearly-button",
                            color="primary",
                            className="mt-3"
                        ),
                        className="text-center"
                    )
                ])
            ])
        ])
    ])
])

@callback(
    [Output('yearly-stats', 'children'),
     Output('yearly-trend-chart', 'figure'),
     Output('yearly-category-chart', 'figure')],
    [Input('url', 'pathname'),
     Input('update-yearly-button', 'n_clicks')]
)
def update_yearly_view(pathname, n_clicks):
    if pathname != "/yearly":
        return no_data_message(), {}, {}
    
    try:
        SPREADSHEET_NAME = "Budget tracker 2025"
        df = pd.DataFrame(get_transactions(SPREADSHEET_NAME, "transactions"))
        # Filter out excluded transactions
        df = df[df['TYPE'] != 'exclude']
        income_cats, expense_cats, saving_cats, investing_cats = get_all_categories_api(SPREADSHEET_NAME)
        
        # Clean and convert values to numeric
        df['VALUE_NUMERIC'] = df['VALUE'].str.replace('Kč', '').str.replace(',', '').astype(float)
        
        # Calculate yearly totals
        total_income = sum_values_by_criteria(df, 'VALUE', CATEGORY=income_cats)
        total_expenses = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=expense_cats))
        total_savings = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=saving_cats))
        total_investments = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=investing_cats))
        net_cashflow = total_income - total_expenses
        
        # Create yearly statistics card
        yearly_stats = html.Div([
            dbc.Row([
                dbc.Col([
                    html.H5("Total Income:", className="text-muted mb-0"),
                    html.H3(f"{total_income:,.2f} Kč", className="text-success")
                ], className="text-center mb-3"),
                dbc.Col([
                    html.H5("Total Expenses:", className="text-muted mb-0"),
                    html.H3(f"{total_expenses:,.2f} Kč", className="text-danger")
                ], className="text-center mb-3")
            ]),
            dbc.Row([
                dbc.Col([
                    html.H5("Total Savings:", className="text-muted mb-0"),
                    html.H3(f"{total_savings:,.2f} Kč", className="text-info")
                ], className="text-center mb-3"),
                dbc.Col([
                    html.H5("Total Investments:", className="text-muted mb-0"),
                    html.H3(f"{total_investments:,.2f} Kč", className="text-primary")
                ], className="text-center mb-3")
            ]),
            html.Hr(),
            html.Div([
                html.H5("Net Cashflow:", className="text-muted mb-0"),
                html.H2(
                    f"{net_cashflow:,.2f} Kč",
                    className=f"{'text-success' if net_cashflow >= 0 else 'text-danger'}"
                )
            ], className="text-center")
        ])
        
        # Create monthly trend chart
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
        trend_fig = px.line(trend_df, x='Month', 
                           y=['Income', 'Expenses', 'Savings', 'Investments'],
                           title='Monthly Financial Trends',
                           labels={'value': 'Amount (Kč)', 'variable': 'Type'},
                           template='plotly_dark')  # Changed to dark theme
        
        # Customize trend chart
        trend_fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title_x=0.5,
            title_font_size=20,
            title_font_color='white',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color='white')
            ),
            xaxis=dict(
                tickangle=45,
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)',
                color='white',
                tickfont=dict(color='white')
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)',
                color='white',
                tickformat=',.0f',
                tickfont=dict(color='white')
            ),
            height=400
        )
        
        # Update line colors and style
        trend_fig.update_traces(
            selector=dict(name='Income'),
            line=dict(color='#2ECC71', width=3),
            mode='lines+markers'
        )
        trend_fig.update_traces(
            selector=dict(name='Expenses'),
            line=dict(color='#E74C3C', width=3),
            mode='lines+markers'
        )
        trend_fig.update_traces(
            selector=dict(name='Savings'),
            line=dict(color='#3498DB', width=3),
            mode='lines+markers'
        )
        trend_fig.update_traces(
            selector=dict(name='Investments'),
            line=dict(color='#9B59B6', width=3),  # Purple color for investments
            mode='lines+markers'
        )
        
        # Create category distribution pie chart
        expenses_by_category = sum_expenses_by_category(df, expense_cats)
        if expenses_by_category:
            category_data = pd.DataFrame({
                'Category': list(expenses_by_category.keys()),
                'Amount': list(expenses_by_category.values())
            })
            
            category_fig = px.pie(
                category_data,
                values='Amount',
                names='Category',
                title='Yearly Expense Distribution',
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
                    orientation="h",
                    y=-0.2,
                    font=dict(color='white')
                ),
                height=400
            )
        else:
            category_fig = empty_chart("No expenses recorded")

        return yearly_stats, trend_fig, category_fig
    except Exception as e:
        print(f"Error updating yearly view: {e}")
        return no_data_message(), {}, {}

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
