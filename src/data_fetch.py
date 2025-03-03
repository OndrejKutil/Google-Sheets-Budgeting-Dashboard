"""Data fetching and caching module for Google Sheets integration.

Provides functions for:
- Fetching data from Google Sheets
- Caching mechanisms to reduce API calls
- Cache configuration management
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from typing import Dict, Any, Optional, Tuple
import json
import os
import backoff
import requests.exceptions
from http.client import RemoteDisconnected
from socket import error as SocketError

CACHE_DURATION = 300  # Cache duration in seconds (5 minutes)
_cache: Dict[str, Tuple[float, Any]] = {}

MAX_RETRIES = 3

def load_settings() -> bool:
    """Load cache settings from the settings file.
    
    Returns:
        bool: True if caching is enabled, False otherwise.
        Creates default settings file if none exists.
    """
    try:
        with open('src/settings.json', 'r') as f:
            settings = json.load(f)
            return settings.get('cache_enabled', True)
    except FileNotFoundError:
        # Create default settings file if it doesn't exist
        settings = {'cache_enabled': True}
        save_settings(True)
        return True

def save_settings(cache_enabled: bool) -> None:
    """Save cache settings to the settings file.
    
    Args:
        cache_enabled: Whether to enable data caching
        
    Raises:
        Exception: If settings file cannot be created or written to
    """
    try:
        os.makedirs('src', exist_ok=True)  # Ensure directory exists
        with open('src/settings.json', 'w') as f:
            json.dump({'cache_enabled': cache_enabled}, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")
        raise

def get_cache_enabled() -> bool:
    """Get current cache setting from settings file.
    
    Returns:
        bool: Current cache state
    """
    try:
        with open('src/settings.json', 'r') as f:
            settings = json.load(f)
            return settings.get('cache_enabled', True)
    except (FileNotFoundError, json.JSONDecodeError):
        save_settings(True)  # Create default settings if file is missing or invalid
        return True

def _get_cache_key(spreadsheet_name: str, worksheet_name: str, **params) -> str:
    """Generate unique cache key for worksheet data.
    
    Args:
        spreadsheet_name: Name of the Google Sheet
        worksheet_name: Name of the worksheet
        **params: Additional parameters that affect the data
    
    Returns:
        str: Unique cache key
    """
    return f"{spreadsheet_name}:{worksheet_name}:{str(params)}"

def _get_cached_data(cache_key: str) -> Optional[Any]:
    """Retrieve data from cache if valid.
    
    Args:
        cache_key: Cache key for the data
        
    Returns:
        Optional[Any]: Cached data if valid, None if expired or disabled
    """
    if not get_cache_enabled():
        return None
    
    cached = _cache.get(cache_key)
    if cached is None:
        return None
    
    timestamp, data = cached
    if time.time() - timestamp > CACHE_DURATION:
        del _cache[cache_key]
        return None
    
    return data

def _set_cached_data(cache_key: str, data: Any) -> None:
    """Store data in cache with current timestamp.
    
    Args:
        cache_key: Cache key for the data
        data: Data to cache
    """
    if get_cache_enabled():
        _cache[cache_key] = (time.time(), data)

def _fetch_from_sheets(client, spreadsheet_name, worksheet_name):
    """Fetch data from Google Sheets with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            sheet = client.open(spreadsheet_name)
            worksheet = sheet.worksheet(worksheet_name)
            return worksheet.get_all_values()
        except Exception as e:
            print(f"Error fetching data (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff

def get_transactions(spreadsheet_name: str, worksheet_name: str) -> list:
    """Fetch transactions from Google Sheet with caching and retry logic."""
    # Check cache first
    cache_key = _get_cache_key(spreadsheet_name, worksheet_name)
    cached_data = _get_cached_data(cache_key)
    if cached_data is not None:
        return cached_data

    try:
        # If not in cache or cache disabled, fetch from sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            './tokens/new-project-01-449515-0a3860dea29d.json', scope)
        client = gspread.authorize(creds)
        
        # Use retry-enabled fetch function
        all_values = _fetch_from_sheets(client, spreadsheet_name, worksheet_name)
        
        if not all_values:
            return []

        headers = all_values[0]  # First row contains headers
        data = all_values[1:]    # Rest is data
        transactions = []
        
        for row in data:
            if len(row) == len(headers):  # Only process rows with correct number of columns
                transaction = dict(zip(headers, row))
                
                # Clean and validate VALUE field
                value = transaction.get('VALUE', '').strip()
                if value == '':
                    value = '0'
                # Remove any currency symbols or separators
                value = value.replace('Kč', '').replace(',', '').replace(' ', '')
                transaction['VALUE'] = value
                
                # Ensure other required fields exist with default values
                transaction.setdefault('TYPE', '')
                transaction.setdefault('CATEGORY', '')
                transaction.setdefault('MONTH', '')
                transaction.setdefault('DESCRIPTION', '')
                
                transactions.append(transaction)

        # Store in cache
        _set_cached_data(cache_key, transactions)
        return transactions

    except Exception as e:
        print(f"Failed to fetch transactions after {MAX_RETRIES} attempts: {str(e)}")
        return []

def get_worksheet(spreadsheet_name: str, worksheet_name: str, 
                 row_start: int, column_start: int, num_columns: Optional[int] = None) -> list:
    """Fetch data from any worksheet with caching.
    
    Args:
        spreadsheet_name: Name of the Google Sheet
        worksheet_name: Name of the worksheet
        row_start: Starting row number (1-based)
        column_start: Starting column number (1-based)
        num_columns: Number of columns to fetch (optional)
        
    Returns:
        list: List of dictionaries with header-value pairs
        
    Raises:
        ValueError: If row_start is less than 1
    """
    # Check cache first
    cache_key = _get_cache_key(spreadsheet_name, worksheet_name, 
                              row_start=row_start, 
                              column_start=column_start, 
                              num_columns=num_columns)
    cached_data = _get_cached_data(cache_key)
    if cached_data is not None:
        return cached_data

    # If not in cache or cache disabled, fetch from sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('./tokens/new-project-01-449515-0a3860dea29d.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(spreadsheet_name)
    worksheet = sheet.worksheet(worksheet_name)
    all_values = worksheet.get_all_values()

    if row_start <= 0:
        raise ValueError("row_start must be greater than 0")

    max_columns = len(all_values[0])
    if num_columns and column_start - 1 + num_columns > max_columns:
        num_columns = max_columns - (column_start - 1)
    headers = all_values[row_start-1][column_start-1:column_start-1+num_columns] if num_columns else all_values[row_start-1][column_start-1:]
    data = [row[column_start-1:column_start-1+num_columns] if num_columns else row[column_start-1:] for row in all_values[row_start:]]

    dataset = [dict(zip(headers, row)) for row in data]

    # Store in cache
    _set_cached_data(cache_key, dataset)
    
    return dataset