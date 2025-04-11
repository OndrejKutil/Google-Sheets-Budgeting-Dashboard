from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np
from data_fetch import get_transactions, load_settings
from get_categories import get_all_categories_api
from analysis import sum_values_by_criteria
import plotly.graph_objects as go
from datetime import datetime
from styles.theme import COLORS, TEXT_STYLES, CHART_THEME
import logging

# Set up logging to file
savings_logger = logging.getLogger('savings')
savings_logger.propagate = False  # Prevent propagation to root logger

# Remove any existing handlers to avoid duplicates
for handler in savings_logger.handlers[:]:
    savings_logger.removeHandler(handler)
    
# Add file handler
file_handler = logging.FileHandler("app_debug.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
savings_logger.addHandler(file_handler)
savings_logger.setLevel(logging.DEBUG)

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

def create_fund_card(fund_name, balance, color="info", icon="piggy-bank"):
    """Create a card for an individual savings fund."""
    # Format balance with commas as thousands separator
    formatted_balance = f"{balance:,.2f} Kč"
    
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"fas fa-{icon} me-2", 
                       style={'fontSize': '1.5rem', 'color': COLORS[color]}),
                html.H5(fund_name, className="card-title mb-1", 
                       style={'color': COLORS['text']})
            ], className="d-flex align-items-center mb-2"),
            html.H4(formatted_balance, 
                   style={'color': COLORS[color], 'fontWeight': 'bold'}),
        ], className="p-3")
    ], className="h-100 shadow-sm")

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
    
    # Second chart row - Updated chart title for Emergency Fund
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
                    html.H4("Emergency Fund Health", 
                           style={'color': COLORS['text']},  # Updated style
                           className="text-center mb-4"),
                    dbc.Spinner(dcc.Graph(id='emergency-fund-chart', figure={}))
                ])
            ])
        ], md=4)
    ]),
    
    # NEW: Add savings fund balance cards grid
    dbc.Row([
        dbc.Col([
            html.H3("Saving Funds Overview", style={'color': COLORS['text']}, className="mb-3"),
            html.Div(id="savings-fund-cards", className="mb-4"),
        ], width=12)
    ], className="mt-4"),
    
    # NEW: Add update button at the bottom
    dbc.Row([
        dbc.Col([
            dbc.Button(
                "Update Data",
                id="update-savings-button",
                color="primary",
                className="mt-4 mb-2",
                size="lg"
            )
        ], className="text-center")
    ])
], fluid=True, style={'backgroundColor': COLORS['background']})  # Added background color

@callback(
    [Output('savings-chart', 'figure'),
     Output('ratio-chart', 'figure'),
     Output('cumulative-chart', 'figure'),
     Output('emergency-fund-chart', 'figure'),  # Changed output ID
     Output('total-savings-card', 'children'),
     Output('total-investments-card', 'children'),
     Output('savings-ratio-card', 'children'),
     Output('investment-ratio-card', 'children'),
     Output('savings-fund-cards', 'children')],  # Added new output for fund cards
    [Input('overview-tabs', 'active_tab'),
     Input('update-savings-button', 'n_clicks')]  # Added button input
)
def update_savings_view(active_tab, n_clicks):
    """Update all dashboard components."""
    try:
        SPREADSHEET_NAME = "Budget tracker 2025"
        df = pd.DataFrame(get_transactions(SPREADSHEET_NAME, "transactions"))
        income_cats, expense_cats, saving_cats, investing_cats = get_all_categories_api(SPREADSHEET_NAME)
        
        # Ensure HISA_FUND column exists, add it if missing
        if 'HISA_FUND' not in df.columns:
            df['HISA_FUND'] = ''
            
        # Calculate total income
        total_income = sum_values_by_criteria(df, 'VALUE', CATEGORY=income_cats)
        
        # Create savings mask based on non-empty HISA_FUND and TYPE=saving
        savings_mask = (df['HISA_FUND'].notna() & 
                       (df['HISA_FUND'].astype(str) != '') & 
                       (df['TYPE'] == 'saving'))
        
        # NEW: Create starting balance mask based on non-empty HISA_FUND and TYPE=start
        starting_balance_mask = (df['HISA_FUND'].notna() & 
                               (df['HISA_FUND'].astype(str) != '') & 
                               (df['TYPE'] == 'start'))
        
        # Get all savings transactions
        df_savings = df[savings_mask].copy()
        
        # NEW: Get all starting balance transactions
        df_starting_balance = df[starting_balance_mask].copy()
        
        # Calculate total savings (deposits)
        total_savings_deposits = abs(sum_values_by_criteria(df_savings, 'VALUE', VALUE_CONDITION='< 0'))
        
        # NEW: Calculate total starting balance
        total_starting_balance = sum_values_by_criteria(df_starting_balance, 'VALUE')
        
        # Create withdrawal mask: HISA_FUND populated + TYPE is 'income'
        withdrawal_mask = (df['HISA_FUND'].notna() & 
                          (df['HISA_FUND'].astype(str) != '') & 
                          (df['TYPE'] == 'income'))
        
        # Get withdrawals from savings funds
        df_withdrawals = df[withdrawal_mask].copy()
        savings_withdrawals = sum_values_by_criteria(df_withdrawals, 'VALUE', VALUE_CONDITION='> 0')
        
        # NEW: Net savings calculation including starting balance
        total_savings = total_starting_balance + total_savings_deposits - savings_withdrawals
        
        # Calculate total investments
        total_investments = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=investing_cats))
        
        # Calculate ratios based on net savings (excluding starting balance for ratio calculation)
        net_contributions = total_savings_deposits - savings_withdrawals
        savings_ratio = (net_contributions / total_income) if total_income > 0 else 0
        investment_ratio = (total_investments / total_income) if total_income > 0 else 0
        
        # Monthly calculations
        all_months = ['January', 'February', 'March', 'April', 'May', 'June', 
                     'July', 'August', 'September', 'October', 'November', 'December']
        monthly_data = []
        
        for month in all_months:
            month_income = sum_values_by_criteria(df, 'VALUE', CATEGORY=income_cats, MONTH=month)
            
            # Monthly savings using the same criteria as total savings
            month_savings_mask = savings_mask & (df['MONTH'] == month)
            month_df_savings = df[month_savings_mask]
            month_savings_deposits = abs(sum_values_by_criteria(month_df_savings, 'VALUE', VALUE_CONDITION='< 0'))
            
            # NEW: Monthly starting balance if it exists for this month
            month_starting_balance_mask = starting_balance_mask & (df['MONTH'] == month)
            month_df_starting_balance = df[month_starting_balance_mask]
            month_starting_balance = sum_values_by_criteria(month_df_starting_balance, 'VALUE')
            
            # Withdrawals from savings
            month_withdrawal_mask = withdrawal_mask & (df['MONTH'] == month)
            month_df_withdrawals = df[month_withdrawal_mask]
            month_savings_withdrawals = sum_values_by_criteria(month_df_withdrawals, 'VALUE', VALUE_CONDITION='> 0')
            
            # Net monthly savings flow (deposits - withdrawals), excluding starting balance
            month_net_flow = month_savings_deposits - month_savings_withdrawals
            
            # Include starting balance in the total monthly savings
            month_total_savings = month_net_flow + month_starting_balance
            
            # Monthly investments (unchanged)
            month_investments = abs(sum_values_by_criteria(df, 'VALUE', CATEGORY=investing_cats, MONTH=month))
            
            # Calculate monthly ratios (prevent division by zero)
            # Only use the net flow for ratio calculation, not starting balance
            month_savings_ratio = (month_net_flow / month_income) if month_income > 0 else 0
            month_investment_ratio = (month_investments / month_income) if month_income > 0 else 0
            
            monthly_data.append({
                'Month': month,
                'Savings': month_total_savings,  # Now includes starting balance
                'Savings Flow': month_net_flow,  # New: just the monthly flow without starting balance
                'Savings Deposits': month_savings_deposits,
                'Savings Withdrawals': month_savings_withdrawals,
                'Starting Balance': month_starting_balance,  # New field
                'Investments': month_investments,
                'Savings Ratio': month_savings_ratio * 100,  # Convert to percentage
                'Investment Ratio': month_investment_ratio * 100  # Convert to percentage
            })
        
        monthly_df = pd.DataFrame(monthly_data)
        
        # Recalculate cumulative savings to include starting balance
        # First add starting balances to the first month that has data
        has_data_mask = (monthly_df['Starting Balance'] > 0) | (monthly_df['Savings Flow'] != 0)
        if has_data_mask.any():
            first_month_idx = has_data_mask.idxmax()
            
            # Initialize cumulative columns
            monthly_df['Cumulative Savings'] = 0
            monthly_df['Cumulative Investments'] = 0
            
            # Set the first month's cumulative savings to include all starting balances
            total_starting = total_starting_balance
            monthly_df.loc[first_month_idx, 'Cumulative Savings'] = total_starting + monthly_df.loc[first_month_idx, 'Savings Flow']
            
            # Cumulatively add savings flow for subsequent months
            for i in range(first_month_idx + 1, len(monthly_df)):
                monthly_df.loc[i, 'Cumulative Savings'] = monthly_df.loc[i-1, 'Cumulative Savings'] + monthly_df.loc[i, 'Savings Flow']
            
            # Calculate cumulative investments
            monthly_df['Cumulative Investments'] = monthly_df['Investments'].cumsum()
            
            # Calculate total wealth
            monthly_df['Total Wealth'] = monthly_df['Cumulative Savings'] + monthly_df['Cumulative Investments']
            
            # Calculate month-over-month changes
            monthly_df['MoM Growth'] = monthly_df['Total Wealth'].pct_change() * 100
            monthly_df['MoM Growth'] = monthly_df['MoM Growth'].fillna(0)  # Replace NaN with 0 for first month
        
        # Calculate emergency fund data for the new chart
        emergency_fund_mask = (df['HISA_FUND'].notna() & 
                              (df['HISA_FUND'].astype(str) == 'Emergency fund') & 
                              (df['TYPE'] == 'saving'))
        
        # Add starting balance for emergency fund
        emergency_starting_mask = (df['HISA_FUND'].notna() & 
                                  (df['HISA_FUND'].astype(str) == 'Emergency fund') & 
                                  (df['TYPE'] == 'start'))
        df_emergency_starting = df[emergency_starting_mask].copy()
        emergency_starting_balance = sum_values_by_criteria(df_emergency_starting, 'VALUE')
        
        # Get all emergency fund transactions
        df_emergency = df[emergency_fund_mask].copy()
        
        # Calculate emergency fund balance (deposits minus withdrawals)
        # For deposits, using abs since values are negative
        emergency_deposits = abs(sum_values_by_criteria(df_emergency, 'VALUE', VALUE_CONDITION='< 0'))
        
        # Check if there are any emergency fund withdrawals (TYPE=income and HISA_FUND='Emergency fund')
        emergency_withdrawal_mask = (df['HISA_FUND'].notna() & 
                                    (df['HISA_FUND'].astype(str) == 'Emergency fund') & 
                                    (df['TYPE'] == 'income'))
        df_emergency_withdrawals = df[emergency_withdrawal_mask].copy()
        emergency_withdrawals = sum_values_by_criteria(df_emergency_withdrawals, 'VALUE', VALUE_CONDITION='> 0')
        
        # Calculate net emergency fund balance including starting balance
        emergency_fund_balance = emergency_starting_balance + emergency_deposits - emergency_withdrawals
        
        # Calculate average monthly expenses (for target calculation)
        expense_mask = df['TYPE'] == 'expense'
        expense_transactions = df[expense_mask].copy()
        
        # Check settings to determine which expenses to use for emergency fund calculation
        settings = load_settings()
        use_fundamental_expenses = settings.get('use_fundamental_expenses', True)  # Default to True if not set
        
        if use_fundamental_expenses and 'NEED' in expense_transactions.columns:
            # Filter for fundamental expenses only
            fundamental_mask = (expense_transactions['NEED'].notna() & 
                               (expense_transactions['NEED'].astype(str).str.lower() == 'fundamental'))
            fundamental_expenses = expense_transactions[fundamental_mask].copy()
            
            # If no fundamental expenses found, fall back to all expenses
            if len(fundamental_expenses) == 0:
                fundamental_expenses = expense_transactions.copy()
        else:
            # Use all expenses if setting is disabled or NEED column doesn't exist
            fundamental_expenses = expense_transactions.copy()
        
        # Calculate total fundamental expenses and average monthly fundamental expenses
        total_fundamental_expenses = abs(sum_values_by_criteria(fundamental_expenses, 'VALUE', VALUE_CONDITION='< 0'))
        
        # Count active months (months with fundamental expenses)
        monthly_fundamental_expenses = {}
        for month in all_months:
            month_expense = abs(sum_values_by_criteria(
                fundamental_expenses, 'VALUE', MONTH=month, VALUE_CONDITION='< 0'))
            if month_expense > 0:
                monthly_fundamental_expenses[month] = month_expense
        
        # Calculate average monthly fundamental expense based on months with data
        num_expense_months = max(len(monthly_fundamental_expenses), 1)  # Avoid division by zero
        avg_monthly_fundamental_expense = total_fundamental_expenses / num_expense_months
        
        # Calculate balances for each saving fund
        fund_balances = calculate_fund_balances(df)
        fund_cards = create_fund_cards_grid(fund_balances)
        
        # Create charts
        fig1 = create_monthly_chart(monthly_df)
        fig2 = create_ratio_chart(monthly_df)
        fig3 = create_cumulative_chart(monthly_df)
        fig4 = create_emergency_fund_chart(avg_monthly_fundamental_expense, emergency_fund_balance, monthly_fundamental_expenses)
        
        return (
            fig1, fig2, fig3, fig4,
            create_stat_card("Total Savings", total_savings, "info"),
            create_stat_card("Total Investments", total_investments, "success"),
            create_stat_card("Savings Ratio", savings_ratio * 100, "info", is_percentage=True),
            create_stat_card("Investment Ratio", investment_ratio * 100, "success", is_percentage=True),
            fund_cards  # Return the fund cards grid
        )
        
    except Exception as e:
        savings_logger.error(f"Error updating savings view: {str(e)}", exc_info=True)
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
            empty_card, empty_card, empty_card, empty_card,
            html.Div()  # Empty div as fallback for fund cards
        )

def calculate_fund_balances(df):
    """Calculate the current balance of each saving fund."""
    # Ensure HISA_FUND column exists
    if 'HISA_FUND' not in df.columns:
        return {}
    
    # Get list of unique fund names
    fund_names = df['HISA_FUND'].dropna().unique()
    fund_balances = {}
    
    # Calculate balance for each fund
    for fund in fund_names:
        if not fund or fund == '':
            continue
            
        # Get starting balance transactions for this fund
        start_mask = (df['HISA_FUND'] == fund) & (df['TYPE'] == 'start')
        starting_balance = sum_values_by_criteria(df[start_mask], 'VALUE')
        
        # Get saving transactions for this fund (deposits are negative in the spreadsheet)
        saving_mask = (df['HISA_FUND'] == fund) & (df['TYPE'] == 'saving')
        deposits = abs(sum_values_by_criteria(df[saving_mask], 'VALUE', VALUE_CONDITION='< 0'))
        
        # Get withdrawal transactions for this fund (withdrawals are positive in the spreadsheet)
        withdrawal_mask = (df['HISA_FUND'] == fund) & (df['TYPE'] == 'income')
        withdrawals = sum_values_by_criteria(df[withdrawal_mask], 'VALUE', VALUE_CONDITION='> 0')
        
        # Calculate total balance
        fund_balance = starting_balance + deposits - withdrawals
        
        # Only include funds with non-zero balance
        if fund_balance != 0:
            fund_balances[fund] = fund_balance
    
    return fund_balances

def create_fund_cards_grid(fund_balances):
    """Create a grid of cards showing balances for each fund."""
    if not fund_balances:
        return html.Div(html.P("No savings funds found.", className="text-muted"))
    
    # Define icons and colors for different fund types
    # Only Emergency fund gets a distinct color, all others share the same color
    fund_icons = {
        'Emergency fund': {'icon': 'shield-alt', 'color': 'primary'},  # Emergency fund gets primary color
        'Health fund': {'icon': 'stethoscope', 'color': 'info'},      # All other funds get info color
        'Education fund': {'icon': 'book', 'color': 'info'},
        'Travel fund': {'icon': 'map-marked-alt', 'color': 'info'},
        'Gear fund': {'icon': 'tools', 'color': 'info'},
        'Clothes fund': {'icon': 'tshirt', 'color': 'info'},
        'Tech fund': {'icon': 'microchip', 'color': 'info'}
    }
    
    # Define priority order for funds (any funds not in this list will be sorted by balance)
    fund_priority = {
        'Emergency fund': 1, 
        'Health fund': 2, 
        'Education fund': 3,
        'Travel fund': 4, 
        'Gear fund': 5, 
        'Clothes fund': 6, 
        'Tech fund': 7
    }
    
    # Custom sorting function: first by priority, then by balance for funds not in priority list
    def sort_funds(fund_item):
        fund_name, balance = fund_item
        return (fund_priority.get(fund_name, 100), -balance)  # Funds not in the list get priority 100
    
    # Sort funds by our custom priority order
    sorted_funds = sorted(fund_balances.items(), key=sort_funds)
    
    # Create card rows (4 cards per row)
    cards = []
    card_rows = []
    fund_count = 0
    
    for fund_name, balance in sorted_funds:
        # Get icon for this fund, use default style if not in predefined list
        icon = fund_icons.get(fund_name, {'icon': 'piggy-bank', 'color': 'info'})['icon']
        
        # Set color: Emergency fund gets its own color, all others use the same color
        color = 'primary' if fund_name == 'Emergency fund' else 'info'
        
        # Create card for this fund
        card = dbc.Col(
            create_fund_card(fund_name, balance, color, icon),
            xs=12, sm=6, md=4, lg=3,
            className="mb-3"
        )
        
        cards.append(card)
        fund_count += 1
        
        # Create a new row after every 4 cards
        if fund_count % 4 == 0:
            card_rows.append(dbc.Row(cards, className="g-3"))
            cards = []
    
    # Add any remaining cards
    if cards:
        card_rows.append(dbc.Row(cards, className="g-3"))
    
    return html.Div(card_rows)

def create_monthly_chart(df):
    """Create monthly savings and investments comparison chart."""
    fig = go.Figure()
    
    # Add savings flow bars (simplified to just include net contributions)
    fig.add_trace(go.Bar(
        name='Net Savings',
        x=df['Month'],
        y=df['Savings Flow'],
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
            font=dict(color=CHART_THEME['font_color'])
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
        font=dict(color=CHART_THEME['font_color'])
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
    
    # Add withdrawal markers with improved positioning and visibility
    withdrawal_df = df[df['Savings Withdrawals'] > 0]
    if not withdrawal_df.empty:
        # Get total height (combined savings + investments) for each withdrawal month
        # to position markers above the stacked area
        total_heights = {}
        for month in withdrawal_df['Month']:
            month_idx = df[df['Month'] == month].index[0]
            total_heights[month] = df.loc[month_idx, 'Cumulative Savings'] + df.loc[month_idx, 'Cumulative Investments']
        
        # Create list of y-positions and hover texts
        y_positions = [total_heights[month] * 1.05 for month in withdrawal_df['Month']]  # 5% above the stacked area
        hover_texts = [f"<b>Withdrawal</b>: {val:,.0f} Kč<br><b>Month</b>: {month}" 
                      for val, month in zip(withdrawal_df['Savings Withdrawals'], withdrawal_df['Month'])]
        
        fig.add_trace(go.Scatter(
            x=withdrawal_df['Month'],
            y=y_positions,
            name='Withdrawals',
            mode='markers+text',
            marker=dict(
                symbol='triangle-down',
                size=12,  # Increased size
                color='rgb(231, 76, 60)',
                line=dict(width=1.5, color='white')  # Increased line width
            ),
            text=["↓" for _ in range(len(withdrawal_df))],
            textposition="top center",
            hoverinfo='text',
            hovertext=hover_texts
        ))
        
        # Add connecting lines from marker to the stacked area
        for i, month in enumerate(withdrawal_df['Month']):
            month_idx = df[df['Month'] == month].index[0]
            cumulative_value = df.loc[month_idx, 'Cumulative Savings'] + df.loc[month_idx, 'Cumulative Investments']
            
            fig.add_shape(
                type="line",
                x0=month, y0=y_positions[i],
                x1=month, y1=cumulative_value,
                line=dict(color="rgb(231, 76, 60)", width=1, dash="dot"),
            )
    
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

def create_emergency_fund_chart(avg_monthly_expense, emergency_fund_balance, monthly_expenses):
    """Create emergency fund health chart comparing to 3 and 6 month expense targets."""
    fig = go.Figure()
    
    # Calculate target levels based on fundamental expenses
    three_month_target = avg_monthly_expense * 3
    six_month_target = avg_monthly_expense * 6
    
    # Create the gauge indicator
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=emergency_fund_balance,
        domain={'x': [0, 1], 'y': [0, 0.85]},  # Reduced height to make more room at bottom
        title={
            'text': "Emergency Fund", 
            'font': {'size': 24, 'color': CHART_THEME['font_color']}
        },
        gauge={
            'axis': {
                'range': [0, six_month_target * 1.1],  # Add 10% padding
                'tickwidth': 1, 
                'tickcolor': CHART_THEME['font_color'],
                'tickvals': [0, three_month_target, six_month_target],
                'ticktext': ['0', '3 months', '6 months'],
                'tickfont': {'color': CHART_THEME['font_color']}
            },
            'bar': {'color': "rgba(46, 204, 113, 0.85)"},
            'bgcolor': "rgba(50, 50, 50, 0.5)",
            'borderwidth': 2,
            'bordercolor': CHART_THEME['axis']['linecolor'],
            'steps': [
                {'range': [0, three_month_target], 'color': "rgba(231, 76, 60, 0.3)"},
                {'range': [three_month_target, six_month_target], 'color': "rgba(241, 196, 15, 0.3)"},
                {'range': [six_month_target, six_month_target * 1.1], 'color': "rgba(46, 204, 113, 0.3)"}
            ],
            'threshold': {
                'line': {'color': "rgba(255, 255, 255, 0.5)", 'width': 2},
                'thickness': 0.75,
                'value': six_month_target
            }
        },
        number={
            'prefix': "",
            'suffix': " Kč",
            'font': {'size': 20, 'color': CHART_THEME['font_color']}
        }
    ))
    
    # Calculate months of expenses coverage - Add check for zero
    months_coverage = 0  # Default value
    if avg_monthly_expense > 0:  # Prevent division by zero
        months_coverage = emergency_fund_balance / avg_monthly_expense
    
    # Add targets information in a single clean text box at the bottom - moved lower
    settings = load_settings()
    expense_type = "fundamental expenses" if settings.get('use_fundamental_expenses', True) else "all expenses"
    
    fig.add_annotation(
        x=0.5, y=-0.15,  # Moved much lower (negative y value)
        text=(
            f"<b>Targets based on {expense_type}:</b><br>"
            f"3 months = {three_month_target:,.0f} Kč | "
            f"6 months = {six_month_target:,.0f} Kč<br>"
            f"Current balance: {emergency_fund_balance:,.0f} Kč "
            f"({months_coverage:.1f} months of expenses)"  # Using the safe value
        ),
        showarrow=False,
        align="center",
        xanchor="center",
        yanchor="top",
        font=dict(size=14, color=CHART_THEME['font_color']),
        bgcolor="rgba(50, 50, 50, 0.7)",
        bordercolor=CHART_THEME['axis']['linecolor'],
        borderpad=6,
        borderwidth=1
    )
    
    fig.update_layout(
        paper_bgcolor=CHART_THEME['bgcolor'],
        plot_bgcolor=CHART_THEME['bgcolor'],
        height=400,
        font=dict(color=CHART_THEME['font_color']),
        margin=dict(t=40, r=25, b=150, l=25),  # Significantly increased bottom margin for the text
        showlegend=False
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
