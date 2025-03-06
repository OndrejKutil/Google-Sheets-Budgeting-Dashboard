"""Category management module for financial transaction classification.

Handles fetching and processing of category definitions from the spreadsheet.
"""

from data_fetch import get_worksheet, cached
import pandas as pd
from typing import List, Tuple

@cached
def get_all_categories_api(spreadsheet_name: str) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Fetch and categorize all transaction categories.
    
    Args:
        spreadsheet_name: Name of the Google Sheets document
    
    Returns:
        tuple: Lists of (income_categories, expense_categories, 
               saving_categories, investing_categories)
        
    Note:
        Categories are defined in the 'definitions' worksheet columns D-F
        starting from row 3.
    """
    # Get definitions worksheet
    definitions = get_worksheet(spreadsheet_name, "definitions", 3, 4, num_columns=3)
    definitions_df = pd.DataFrame(definitions)

    # Validate columns
    required_columns = ['Category Type', 'Category Description']
    for column in required_columns:
        if column not in definitions_df.columns:
            raise ValueError(f"Missing required column: {column}")

    # Get categories by type
    income_categories = definitions_df[definitions_df['Category Type'] == 'income']['Category Description'].tolist()
    expense_categories = definitions_df[definitions_df['Category Type'] == 'expense']['Category Description'].tolist()
    saving_categories = definitions_df[definitions_df['Category Type'] == 'saving']['Category Description'].tolist()
    investing_categories = definitions_df[definitions_df['Category Type'] == 'investment']['Category Description'].tolist()

    return income_categories, expense_categories, saving_categories, investing_categories