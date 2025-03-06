# Data Fetching and Analysis Documentation

This document covers the data fetching, caching, and analysis components of the Budget Dashboard application.

## Table of Contents
1. [Data Fetching](#data-fetching)
2. [Caching System](#caching-system)
3. [Data Analysis](#data-analysis)
4. [Category Management](#category-management)

## Data Fetching

The application fetches financial data from Google Sheets using the `gspread` and `oauth2client` libraries.

### Core Functions

#### `get_transactions()`

```python
def get_transactions(spreadsheet_name: str, worksheet_name: str) -> list:
    """Fetch transactions from Google Sheet with caching and retry logic."""
```

This function retrieves transaction data from a specified Google Sheet worksheet:
- **Parameters**: Spreadsheet name and worksheet name
- **Returns**: List of transaction dictionaries
- **Features**: 
  - Implements caching to reduce API calls
  - Includes retry logic with exponential backoff
  - Cleans and validates data fields
  - Sets default values for missing fields

#### `get_worksheet()`

```python
def get_worksheet(spreadsheet_name: str, worksheet_name: str,
                 row_start: int, column_start: int, num_columns: Optional[int] = None) -> list:
    """Fetch data from any worksheet with caching."""
```

A more flexible function for fetching arbitrary worksheet data:
- **Parameters**: Spreadsheet name, worksheet name, starting row/column, and optional column count
- **Returns**: List of dictionaries with header-value pairs
- **Features**:
  - Supports partial worksheet retrieval
  - Parameter validation
  - Handles API errors

## Caching System

The application implements a sophisticated caching system to optimize performance and reduce API calls.

### Cache Configuration

Settings are stored in `settings.json` and include:
- `cache_enabled`: Toggle for caching functionality
- `cache_duration`: Time in seconds before cache entries expire
- `prefetch_enabled`: Toggle for automatic prefetching of common data
- `debug_mode`: Toggle for additional debug information

### Cache Functions

#### `load_settings()` and `save_settings()`
Manage application settings with defaults and error handling.

#### `cached()` Decorator
```python
@cached
def function_name():
    # Function code
```

A decorator that automatically caches function results based on parameters.

#### Cache Control Functions
- `clear_cache()`: Remove all cached data
- `get_cache_stats()`: Return metrics about cache performance
- `prefetch_common_data()`: Preload frequently accessed data

### Cache Statistics

The cache system tracks:
- Hit count: Number of successful cache retrievals
- Miss count: Number of failed cache retrievals
- Hit rate: Percentage of cache hits vs. total requests
- Cache size: Number of items currently cached
- API calls saved: Estimated API calls prevented by caching
- Cache age: Time since last cache clear

## Data Analysis

The analysis module (`analysis.py`) provides functions for analyzing financial data:

### Core Analysis Functions

#### `sum_values_by_criteria()`

```python
def sum_values_by_criteria(transactions: pd.DataFrame, value_key: str, **criteria) -> float:
    """Sum transaction values based on given criteria."""
```

This is the main filtering and aggregation function:
- Filters transactions by flexible criteria
- Converts string values to numeric format
- Returns the sum of matching transactions

#### `sum_expenses_by_category()`

Aggregates expenses by category, optionally filtered by month.

#### `compute_cashflow()`

Calculates cashflow (income minus expenses) for a given period.

#### `calculate_expense_ratio()`

Determines the ratio of expenses to income as a percentage.

#### `top_5_highest_transactions()`

Identifies the top 5 largest transactions in a given category.

## Category Management

The `get_categories.py` module categorizes transactions into:
- Income categories
- Expense categories
- Saving categories
- Investment categories

### Functions

#### `get_all_categories_api()`

```python
@cached
def get_all_categories_api(spreadsheet_name: str) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Fetch and categorize all transaction categories."""
```

This decorated function:
- Retrieves category definitions from the "definitions" worksheet
- Validates required columns exist
- Groups categories by type (income, expense, saving, investment)
- Returns categorized lists for use throughout the application
- Utilizes caching to improve performance
