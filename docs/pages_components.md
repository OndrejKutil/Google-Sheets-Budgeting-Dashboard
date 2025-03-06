# Pages and Components Documentation

This document covers the individual pages and UI components of the Budget Dashboard application.

## Table of Contents
1. [Overview Page](#overview-page)
2. [Monthly Analysis Page](#monthly-analysis-page)
3. [Transactions Page](#transactions-page)
4. [Accounts Page](#accounts-page)
5. [Savings Page](#savings-page)
6. [Setup Page](#setup-page)
7. [Common UI Components](#common-ui-components)

## Overview Page

The Overview page (`overview_page.py`) serves as the primary dashboard with multiple tabs:

```python
layout = dbc.Container([
    html.H1("Financial Overview", style=TEXT_STYLES['h1']),
    dbc.Tabs([
        dbc.Tab(yearly_layout, label="Yearly Overview", tab_id="yearly-tab"),
        dbc.Tab(monthly_layout, label="Monthly Overview", tab_id="monthly-tab"),
        dbc.Tab(savings_layout, label="Savings & Investments", tab_id="savings-tab"),
    ], id="overview-tabs", active_tab="yearly-tab")
])
```

### Yearly Overview Tab

Located in `yearly_page.py`, this tab provides:

1. **Overview Section**
   - Key financial statistics (income, expenses, savings, investments)
   - Category distribution pie chart

2. **Expenses Section**
   - Monthly expenses chart
   - Expense trends
   - Spending heatmap

3. **Income Section**
   - Monthly income chart
   - Income sources distribution

All visualizations include callbacks that update when:
- The active tab changes
- The update button is clicked

### Monthly Analysis Tab

See [Monthly Analysis Page](#monthly-analysis-page) below.

### Savings & Investments Tab

The savings tab (`savings_page.py`) focuses on wealth-building metrics:

1. **Statistics Cards**
   - Total savings and investments
   - Savings and investment ratios

2. **Charts**
   - Monthly savings and investments
   - Monthly ratios
   - Cumulative growth
   - Month-over-month performance

## Monthly Analysis Page

The Monthly Analysis page (`monthly_page.py`) provides detailed monthly insights:

```python
layout = dbc.Container([
    # Month selector
    dbc.Row([...]),
    
    # Statistics cards (income, expenses, net income, expense ratio)
    dbc.Row([...]),
    
    # Charts (comparison, distribution)
    dbc.Row([...]),
    
    # Bottom row (daily expenses, top expenses)
    dbc.Row([...])
])
```

### Key Features

1. **Month Selector**
   - Dropdown menu for selecting the month
   - Update button to refresh data

2. **Statistics Cards**
   - Income, expenses, net income, and expense ratio
   - Color-coded for quick understanding

3. **Visualization Charts**
   - Monthly expenses by category
   - Expense distribution pie chart
   - Daily expenses trend with rolling average
   - Top expenses table

## Transactions Page

The Transactions page (`transactions_page.py`) displays raw transaction data:

```python
layout = dbc.Container([
    html.H1("Transactions", className="my-4", style=TEXT_STYLES['h1']),
    
    dash_table.DataTable(
        id='transactions-table',
        # Table configuration
    )
])
```

### DataTable Features

1. **Data Handling**
   - Pagination with 25 transactions per page
   - Multi-column sorting
   - Case-insensitive filtering
   - Automatic loading to latest page

2. **Styling**
   - Consistent with application theme
   - Conditional styling for expenses (red) and income (green)
   - Alternating row colors
   - Custom styling for selected cells

3. **Callbacks**
   - Data refresh when navigating to the page

## Accounts Page

The Accounts page (`accounts_page.py`) displays account balances and distribution:

```python
layout = dbc.Container([
    html.H1("Accounts Overview", className="my-4", style=TEXT_STYLES['h1']),
    dbc.Row([
        # Account balances table
        dbc.Col([...], md=6),
        # Account distribution pie chart
        dbc.Col([...], md=6)
    ])
])
```

### Key Features

1. **Account Balances**
   - Table of all accounts and their current balances
   - Total sum of all accounts
   - Automatic calculation from transaction data

2. **Distribution Visualization**
   - Pie chart of account distribution
   - Color-coded by account type
   - Percentage labels

## Savings Page

The Savings page (`savings_page.py`) focuses on long-term financial growth:

```python
layout = dbc.Container([
    html.H1("Savings & Investments Overview", style={'color': COLORS['text']}, className="my-4"),
    
    # Statistics cards row
    dbc.Row([...]),
    
    # First chart row (Monthly Savings & Investments, Monthly Ratios)
    dbc.Row([...]),
    
    # Second chart row (Cumulative Growth, Monthly Performance)
    dbc.Row([...])
])
```

### Key Visualizations

1. **Monthly Comparison**
   - Bar chart comparing monthly savings and investments
   - Grouped bars for direct comparison

2. **Ratio Tracking**
   - Line chart showing savings and investment ratios
   - Target lines for reference

3. **Cumulative Growth**
   - Stacked area chart showing total wealth growth
   - Breakdown by savings vs. investments

4. **Performance Metrics**
   - Bar chart with month-over-month growth rates
   - Color-coded for positive/negative periods

## Setup Page

The Setup page (`setup_page.py`) provides application configuration:

```python
layout = dbc.Container([
    dcc.Location(id='setup-url', refresh=True),
    html.H1("Setup", className="my-4"),
    dbc.Card([
        dbc.CardBody([
            html.H4("Cache Settings"),
            # Cache options
            # Cache statistics
            # API connection test
        ])
    ])
])
```

### Configuration Options

1. **Cache Settings**
   - Enable/disable data caching
   - Enable/disable data prefetching
   - Set cache duration (30-3600 seconds)
   - Clear cache button

2. **Cache Statistics**
   - Cache size, hits, misses
   - Hit rate and API calls saved
   - Cache age

3. **API Connection Test**
   - Test connection button
   - Connection status indicator

## Common UI Components

### Stat Cards

```python
def create_stat_card(title, value, color="primary", is_percentage=False):
    """Create a statistics card with consistent styling."""
    return dbc.Card([
        dbc.CardBody([
            html.H6(title, style={'color': COLORS['text_muted']}),
            html.H4(f"{value:,.2f}{'%' if is_percentage else ' Kč'}", style={'color': COLORS[color]})
        ], className="p-2")
    ], className="h-100")
```

Statistics cards are used throughout the application for key metrics.

### Chart Creation Functions

Each page includes specialized chart creation functions:

```python
def create_comparison_chart(df, income_cats, expense_cats):
    """Create expenses bar chart."""
    # Chart creation code
```

These functions standardize chart appearance with:
- Consistent color schemes
- Standardized layout parameters
- Common hover formatting
- Responsive sizing

### Tables

```python
def create_top_expenses_table(df):
    """Create styled top expenses table."""
    return dbc.Table([
        # Table definition
    ], bordered=True, dark=True, hover=True)
```

Tables include:
- Consistent styling with the application theme
- Conditional formatting for data values
- Responsive design for different screen sizes
