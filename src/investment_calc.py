import pandas as pd
import numpy as np

def calculate_investment_growth(initial_sum: float,
                             monthly_investment: float,
                             annual_return: float,
                             years: int) -> pd.DataFrame:
    """Calculate investment growth over time with monthly contributions.
    
    Args:
        initial_sum: Starting investment amount
        monthly_investment: Monthly contribution amount
        annual_return: Expected annual return rate (as percentage)
        years: Number of years to project
        
    Returns:
        DataFrame with columns: Month, Value, Invested, Gains
    """
    # Convert annual return to monthly
    monthly_return = (1 + annual_return/100) ** (1/12) - 1
    
    # Create monthly timeline using 'ME' (month end) instead of deprecated 'M'
    months = years * 12
    timeline = pd.date_range(start='today', periods=months+1, freq='ME')
    
    # Initialize arrays
    values = np.zeros(months + 1)
    invested = np.zeros(months + 1)
    
    # Set initial values
    values[0] = initial_sum
    invested[0] = initial_sum
    
    # Calculate growth month by month
    for month in range(1, months + 1):
        # Add monthly investment
        invested[month] = invested[month-1] + monthly_investment
        # Calculate growth
        values[month] = (values[month-1] * (1 + monthly_return)) + monthly_investment
    
    # Create DataFrame
    df = pd.DataFrame({
        'Month': timeline,
        'Value': values,
        'Invested': invested,
        'Gains': values - invested
    })
    
    return df
