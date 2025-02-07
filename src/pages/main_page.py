import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output
import plotly.express as px
import pandas as pd
from data_fetch import get_transactions
from get_categories import get_all_categories_api
from analysis import sum_values_by_criteria

"""Main page showing overall financial trends throughout the year."""

layout = dbc.Container([
    html.H1("Financial Overview", className="my-4"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Income and Expenses by Month", className="text-center mb-4"),
                    dbc.Spinner(
                        dcc.Graph(
                            id='monthly-chart',
                            figure={}
                        )
                    ),
                    html.Div([
                        dbc.Button(
                            "Update Chart",
                            id="update-chart-button",
                            color="primary",
                            className="mt-3"
                        )
                    ], className="text-center")
                ])
            ])
        ])
    ])
])

@callback(
    Output('monthly-chart', 'figure'),
    [Input('update-chart-button', 'n_clicks')],
    prevent_initial_call=False
)
def update_monthly_chart(n_clicks) -> dict:
    """Update the main overview chart showing income, expenses and net values by month.

    Returns:
        dict: Plotly figure object containing the chart
    """
    try:
        SPREADSHEET_NAME = "Budget tracker 2025"
        df = pd.DataFrame(get_transactions(SPREADSHEET_NAME, "transactions"))
        # Filter out excluded transactions
        df = df[df['TYPE'] != 'exclude']
        income_cats, expense_cats, _, _ = get_all_categories_api(SPREADSHEET_NAME)
        
        # Define all months for consistent x-axis
        all_months = ['January', 'February', 'March', 'April', 'May', 'June', 
                     'July', 'August', 'September', 'October', 'November', 'December']
        
        # Calculate monthly income and expenses
        monthly_data = []
        
        # Process data for each month
        for month in all_months:
            # Create a proper copy of the filtered data
            month_df = df[df['MONTH'] == month].copy(deep=True)
            
            if len(month_df) > 0:
                # Use loc for assignment
                month_df.loc[:, 'VALUE'] = (month_df['VALUE']
                                          .str.replace('Kč', '')
                                          .str.replace(',', '')
                                          .astype(float))
                
                income = sum_values_by_criteria(month_df, 'VALUE', CATEGORY=income_cats)
                expenses = abs(sum_values_by_criteria(month_df, 'VALUE', CATEGORY=expense_cats))
                
                monthly_data.append({
                    'Month': month,
                    'Income': income if income != 0 else 0,
                    'Expenses': expenses if expenses != 0 else 0,
                    'Net': income - expenses  # Net is always calculated, even if zero
                })
            else:
                # For months with no data, use None for Income/Expenses but 0 for Net
                monthly_data.append({
                    'Month': month,
                    'Income': None,
                    'Expenses': None,
                    'Net': 0  # Changed from None to 0
                })
        
        monthly_df = pd.DataFrame(monthly_data)
        
        # Create line chart with custom styling
        fig = px.line(monthly_df, x='Month', y=['Income', 'Expenses', 'Net'],
                     title='Monthly Financial Overview',
                     labels={'value': 'Amount (Kč)', 'variable': 'Type'},
                     template='plotly_dark')  # Changed from plotly_white to plotly_dark
        
        # Customize the layout
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
            plot_bgcolor='rgba(0,0,0,0)',   # Transparent plot area
            title_x=0.5,
            title_font_size=24,
            title_font_color='white',       # White title text
            legend_title_text='',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color='white')    # White legend text
            ),
            xaxis=dict(
                tickangle=45,
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)',  # Subtle grid lines
                color='white',              # White axis text
                tickfont=dict(color='white')
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)',  # Subtle grid lines
                color='white',              # White axis text
                tickformat=',.0f',
                tickfont=dict(color='white')
            ),
            height=600,
            margin=dict(t=100)
        )
        
        # Update line styling - keep existing colors but make lines brighter
        fig.update_traces(
            selector=dict(name='Income'),
            line=dict(color='#2ECC71', width=3),
            mode='lines+markers'
        )
        fig.update_traces(
            selector=dict(name='Expenses'),
            line=dict(color='#E74C3C', width=3),
            mode='lines+markers'
        )
        fig.update_traces(
            selector=dict(name='Net'),
            line=dict(color='#3498DB', width=3),
            mode='lines+markers'
        )
        
        return fig
    except Exception as e:
        print(f"Error updating chart: {e}")
        return {}
