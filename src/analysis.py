"""Analysis module for financial calculations and data processing.

This module provides functions for analyzing financial data including:
- Transaction summaries
- Category-based calculations
- Cashflow analysis
- Expense ratio calculations
"""

import pandas as pd
from typing import Dict, List, Optional

def sum_values_by_criteria(transactions: pd.DataFrame, value_key: str, **criteria) -> float:
    """Sum transaction values based on given criteria.
    
    Args:
        transactions: DataFrame containing financial transactions
        value_key: Column name containing monetary values
        **criteria: Key-value pairs for filtering (e.g., CATEGORY=['Food', 'Transport'])
                   Special key VALUE_CONDITION can be used for value comparisons (e.g., '> 0')
    
    Returns:
        float: Sum of filtered values
    """
    if transactions.empty:
        return 0.0
        
    filtered_df = transactions.copy()
    
    # Check if value_key exists in columns
    if value_key not in filtered_df.columns:
        return 0.0
    
    # First ensure we're working with strings before applying string operations
    filtered_df[value_key] = filtered_df[value_key].astype(str)
    filtered_df[value_key] = (filtered_df[value_key]
                             .str.replace('Kč', '')
                             .str.replace(',', '')
                             .str.strip()
                             .astype(float))
    
    # Special handling for VALUE_CONDITION
    if 'VALUE_CONDITION' in criteria:
        value_condition = criteria.pop('VALUE_CONDITION')
        try:
            filtered_df = filtered_df.query(f"{value_key} {value_condition}")
        except Exception as e:
            # If query fails, try manual filtering
            if '>' in value_condition:
                threshold = float(value_condition.replace('>', '').strip())
                filtered_df = filtered_df[filtered_df[value_key] > threshold]
            elif '<' in value_condition:
                threshold = float(value_condition.replace('<', '').strip())
                filtered_df = filtered_df[filtered_df[value_key] < threshold]
    
    # Process remaining criteria
    for key, value in criteria.items():
        if key not in filtered_df.columns:
            continue
            
        if isinstance(value, list):
            filtered_df = filtered_df[filtered_df[key].isin(value)]
        elif isinstance(value, str) and any(op in value for op in ['>', '<', '>=', '<=', '==', '!=']):
            try:
                filtered_df = filtered_df.query(f"{key} {value}")
            except Exception:
                pass
        else:
            filtered_df = filtered_df[filtered_df[key] == value]
    
    return filtered_df[value_key].sum()


def top_5_highest_transactions(transactions: pd.DataFrame, category: str) -> pd.DataFrame:
    """Return the top 5 highest transactions for a given category.

    Args:
        transactions (DataFrame): dataframe containing the transactions
        category (str): category to filter by

    Returns:
        DataFrame: top 5 highest transactions in the given category
    """

    # Create a copy to avoid modifying the original DataFrame
    filtered_df = transactions[transactions['CATEGORY'] == category].copy()
    
    # Clean the VALUE column: remove currency symbol, spaces, and commas
    filtered_df['VALUE_NUMERIC'] = (filtered_df['VALUE']
                                  .str.replace('Kč', '')
                                  .str.replace(',', '')
                                  .str.strip()
                                  .astype(float))
    
    # Get top 5 using the numeric column
    top_5_df = filtered_df.nlargest(5, 'VALUE_NUMERIC')
    
    # Drop the temporary numeric column
    top_5_df = top_5_df.drop('VALUE_NUMERIC', axis=1)
        
    return top_5_df


def sum_expenses_by_category(df, expense_cats, month=None):
    """Sum expenses by category, optionally filtered by month.

    Args:
        df (DataFrame): DataFrame containing the transactions
        expense_cats (list): List of expense category names
        month (str, optional): Month name to filter by. Defaults to None.

    Returns:
        dict: Dictionary with categories as keys and summed expenses as values
    """
    # First convert the values to numeric
    df = df.copy()
    # Ensure string type before string operations
    df['VALUE'] = df['VALUE'].astype(str)
    df['VALUE_NUMERIC'] = (df['VALUE']
                          .str.replace('Kč', '')
                          .str.replace(',', '')
                          .str.strip()
                          .astype(float))
    
    # Filter by month if specified
    if month:
        df = df[df['MONTH'] == month]
    
    # Only include expense categories and negative values
    df = df[
        (df['CATEGORY'].isin(expense_cats)) & 
        (df['VALUE_NUMERIC'] < 0)
    ]
    
    # Group by category and sum absolute values
    expenses = df.groupby('CATEGORY')['VALUE_NUMERIC'].sum().abs()
    
    # Convert to dictionary and filter out zero values
    expenses_dict = expenses[expenses > 0].to_dict()
    
    return expenses_dict if expenses_dict else {'No Expenses': 0}  # Return default if no expenses


def compute_cashflow(transactions: pd.DataFrame, income_categories: list, expense_categories: list, month: str = None) -> float:
    """Calculate cashflow (income - expenses), optionally filtered by month.

    Args:
        transactions (DataFrame): dataframe containing the transactions
        income_categories (list): List of income category names
        expense_categories (list): List of expense category names
        month (str, optional): Month name to filter by. Defaults to None.

    Returns:
        float: Cashflow value (positive means profit, negative means loss)
    """
    if month:
        total_income = sum_values_by_criteria(transactions, 'VALUE', CATEGORY=income_categories, MONTH=month)
        total_expenses = sum_values_by_criteria(transactions, 'VALUE', CATEGORY=expense_categories, MONTH=month)
    else:
        total_income = sum_values_by_criteria(transactions, 'VALUE', CATEGORY=income_categories)
        total_expenses = sum_values_by_criteria(transactions, 'VALUE', CATEGORY=expense_categories)
    
    return total_income + total_expenses


def calculate_expense_ratio(transactions: pd.DataFrame, income_categories: list, expense_categories: list, month: str = None) -> float:
    """Calculate the ratio of expenses to income (expenses/income).

    Args:
        transactions (DataFrame): dataframe containing the transactions
        income_categories (list): List of income category names
        expense_categories (list): List of expense category names
        month (str, optional): Month name to filter by. Defaults to None.

    Returns:
        float: Expense ratio (0.7 means spending 70% of income)
    """
    if month:
        total_income = sum_values_by_criteria(transactions, 'VALUE', CATEGORY=income_categories, MONTH=month)
        total_expenses = abs(sum_values_by_criteria(transactions, 'VALUE', CATEGORY=expense_categories, MONTH=month))
    else:
        total_income = sum_values_by_criteria(transactions, 'VALUE', CATEGORY=income_categories)
        total_expenses = abs(sum_values_by_criteria(transactions, 'VALUE', CATEGORY=expense_categories))
    
    if total_income == 0:
        return float('inf')
    
    return total_expenses / total_income


"""
ratio = calculate_expense_ratio(df, income_categories, expense_categories)
print(f"Overall expense ratio: {ratio:.2%}")  # Formats as percentage
january_ratio = calculate_expense_ratio(df, income_categories, expense_categories, month='January')
print(f"January expense ratio: {january_ratio:.2%}")

# Sum all income and all expenses in January
total_income_january = sum_values_by_criteria(df, 'VALUE', CATEGORY=income_categories, MONTH='January')
total_expenses_january = sum_values_by_criteria(df, 'VALUE', CATEGORY=expense_categories, MONTH='January')

print(f"Total income in January: {total_income_january:.2f} Kč")
print(f"Total expenses in January: {total_expenses_january:.2f} Kč")


cashflow = compute_cashflow(df, income_categories, expense_categories)
print(f"\nTotal cashflow: {cashflow:.2f} Kč")

january_cashflow = compute_cashflow(df, income_categories, expense_categories, month='January')
print(f"January cashflow: {january_cashflow:.2f} Kč")

expenses_summary = sum_expenses_by_category(df, expense_categories)
print("\nAll expenses:")
for category, amount in expenses_summary.items():
    print(f"{category}: {amount:.2f} Kč")

january_expenses = sum_expenses_by_category(df, expense_categories, month='January')
print("\nJanuary expenses:")
for category, amount in january_expenses.items():
    print(f"{category}: {amount:.2f} Kč")

top_5_income_transactions = top_5_highest_transactions(df, 'Interest/dividents')
print(top_5_income_transactions)
"""
