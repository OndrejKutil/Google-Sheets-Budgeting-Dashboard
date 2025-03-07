"""Data fetching and caching module for Google Sheets integration.

Provides functions for:
- Fetching data from Google Sheets
- Caching mechanisms to reduce API calls
- Cache configuration management
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from typing import Dict, Any, Optional, Tuple, List, Callable
import json
import os
import functools
import logging

TOKEN_FILE_PATH = './tokens/new-project-01-449515-0a3860dea29d.json'

# Default cache settings
DEFAULT_CACHE_DURATION = 300  # Default cache duration in seconds (5 minutes)
_cache: Dict[str, Tuple[float, Any]] = {}
_cache_stats = {
    'hits': 0,
    'misses': 0,
    'size': 0,
    'saved_api_calls': 0,
    'last_cleared': time.time()
}

MAX_RETRIES = 3

# Set up logging to only write to file
cache_logger = logging.getLogger('cache')
# Remove any existing handlers
for handler in cache_logger.handlers[:]:
    cache_logger.removeHandler(handler)
# Prevent propagation to root logger
cache_logger.propagate = False
# Add file handler
file_handler = logging.FileHandler("app_debug.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
cache_logger.addHandler(file_handler)
cache_logger.setLevel(logging.INFO)

def load_settings() -> dict:
    """Load cache settings from the settings file.
    
    Returns:
        dict: Dictionary with all settings
        Creates default settings file if none exists.
    """
    default_settings = {
        'cache_enabled': True,
        'cache_duration': DEFAULT_CACHE_DURATION,
        'prefetch_enabled': True,
        'debug_mode': False
    }
    
    try:
        with open('src/settings.json', 'r') as f:
            settings = json.load(f)
            # Update with any missing default settings
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
            return settings
    except FileNotFoundError:
        # Create default settings file if it doesn't exist
        save_settings(default_settings)
        return default_settings
    except json.JSONDecodeError:
        # Handle corrupted settings file
        cache_logger.warning("Corrupted settings file. Creating new default settings.")
        save_settings(default_settings)
        return default_settings

def save_settings(settings_dict: dict) -> None:
    """Save cache settings to the settings file.
    
    Args:
        settings_dict: Dictionary with settings to save
        
    Raises:
        Exception: If settings file cannot be created or written to
    """
    try:
        os.makedirs('src', exist_ok=True)  # Ensure directory exists
        with open('src/settings.json', 'w') as f:
            json.dump(settings_dict, f, indent=4)
    except Exception as e:
        cache_logger.error(f"Error saving settings: {e}")
        raise

def get_cache_enabled() -> bool:
    """Get current cache setting from settings file.
    
    Returns:
        bool: Current cache state
    """
    settings = load_settings()
    return settings.get('cache_enabled', True)

def get_cache_duration() -> int:
    """Get current cache duration setting from settings file.
    
    Returns:
        int: Cache duration in seconds
    """
    settings = load_settings()
    return settings.get('cache_duration', DEFAULT_CACHE_DURATION)

def get_cache_stats() -> dict:
    """Get statistics about the cache usage.
    
    Returns:
        dict: Dictionary with cache statistics
    """
    stats = _cache_stats.copy()
    
    # Calculate hit rate
    total_requests = stats['hits'] + stats['misses']
    stats['hit_rate'] = stats['hits'] / total_requests if total_requests > 0 else 0
    
    # Calculate current size
    stats['current_size'] = len(_cache)
    
    # Calculate age
    stats['cache_age_seconds'] = time.time() - stats['last_cleared']
    
    return stats

def clear_cache() -> None:
    """Clear all cached data and reset statistics."""
    global _cache, _cache_stats
    _cache.clear()
    _cache_stats['last_cleared'] = time.time()
    _cache_stats['size'] = 0
    cache_logger.info("Cache cleared")

def _get_cache_key(spreadsheet_name: str, worksheet_name: str, **params) -> str:
    """Generate unique cache key for worksheet data.
    
    Args:
        spreadsheet_name: Name of the Google Sheet
        worksheet_name: Name of the worksheet
        **params: Additional parameters that affect the data
    
    Returns:
        str: Unique cache key
    """
    param_str = json.dumps(params, sort_keys=True) if params else ""
    return f"{spreadsheet_name}:{worksheet_name}:{param_str}"

def _get_cached_data(cache_key: str) -> Optional[Any]:
    """Retrieve data from cache if valid.
    
    Args:
        cache_key: Cache key for the data
        
    Returns:
        Optional[Any]: Cached data if valid, None if expired or disabled
    """
    if not get_cache_enabled():
        _cache_stats['misses'] += 1
        return None
    
    cached = _cache.get(cache_key)
    if cached is None:
        _cache_stats['misses'] += 1
        return None
    
    timestamp, data = cached
    cache_duration = get_cache_duration()
    
    if time.time() - timestamp > cache_duration:
        # Cache expired
        del _cache[cache_key]
        _cache_stats['size'] = len(_cache)
        _cache_stats['misses'] += 1
        return None
    
    # Cache hit
    _cache_stats['hits'] += 1
    _cache_stats['saved_api_calls'] += 1
    return data

def _set_cached_data(cache_key: str, data: Any) -> None:
    """Store data in cache with current timestamp.
    
    Args:
        cache_key: Cache key for the data
        data: Data to cache
    """
    if get_cache_enabled():
        _cache[cache_key] = (time.time(), data)
        _cache_stats['size'] = len(_cache)
        
        # Log cache size every 10 entries
        if _cache_stats['size'] % 10 == 0:
            cache_logger.info(f"Cache size: {_cache_stats['size']} entries")

def cached(func: Callable) -> Callable:
    """Decorator for caching function results.
    
    Uses the function name and arguments to create a cache key.
    
    Args:
        func: Function to decorate
        
    Returns:
        Callable: Decorated function with caching
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not get_cache_enabled():
            return func(*args, **kwargs)
        
        # Create a cache key from function name and arguments
        key_parts = [func.__name__]
        key_parts.extend([str(arg) for arg in args])
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        cache_key = ":".join(key_parts)
        
        # Check cache
        cached_data = _get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Execute function and cache result
        result = func(*args, **kwargs)
        _set_cached_data(cache_key, result)
        return result
    
    return wrapper

def _fetch_from_sheets(client, spreadsheet_name, worksheet_name):
    """Fetch data from Google Sheets with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            sheet = client.open(spreadsheet_name)
            worksheet = sheet.worksheet(worksheet_name)
            return worksheet.get_all_values()
        except Exception as e:
            cache_logger.warning(f"Error fetching data (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff

def prefetch_common_data() -> None:
    """Prefetch commonly accessed data into cache.
    
    This reduces API calls for frequently accessed data.
    """
    settings = load_settings()
    if not settings.get('prefetch_enabled', False):
        return
    
    try:
        cache_logger.info("Prefetching common data...")
        SPREADSHEET_NAME = "Budget tracker 2025"
        
        start_time = time.time()
        
        # Prefetch transactions
        transactions = get_transactions(SPREADSHEET_NAME, "transactions")
        cache_logger.info(f"Prefetched {len(transactions)} transactions")
        
        # Prefetch definitions
        definitions = get_worksheet(SPREADSHEET_NAME, "definitions", 3, 4, num_columns=3)
        cache_logger.info(f"Prefetched {len(definitions)} category definitions")
        
        # Log successful prefetch with timing - only once
        elapsed = time.time() - start_time
        cache_logger.info(f"Prefetch complete in {elapsed:.2f} seconds")
    except Exception as e:
        cache_logger.error(f"Error during prefetch: {e}")

def get_transactions(spreadsheet_name: str, worksheet_name: str) -> list:
    """Fetch transactions from Google Sheet with caching and retry logic."""
    start_time = time.time()
    
    # Check cache first
    cache_key = _get_cache_key(spreadsheet_name, worksheet_name)
    cached_data = _get_cached_data(cache_key)
    if cached_data is not None:
        cache_logger.debug(f"Retrieved {len(cached_data)} transactions from cache in {time.time() - start_time:.3f}s")
        return cached_data

    try:
        cache_logger.debug(f"Cache miss for {spreadsheet_name}/{worksheet_name}, fetching from API")
        # If not in cache or cache disabled, fetch from sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            TOKEN_FILE_PATH, scope)
        client = gspread.authorize(creds)
        
        # Use retry-enabled fetch function
        all_values = _fetch_from_sheets(client, spreadsheet_name, worksheet_name)
        
        if not all_values:
            cache_logger.warning(f"No data returned from worksheet {worksheet_name}")
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
        
        # Log performance info
        elapsed = time.time() - start_time
        cache_logger.info(f"Fetched {len(transactions)} transactions from API in {elapsed:.3f}s")
        
        return transactions

    except Exception as e:
        cache_logger.error(f"Failed to fetch transactions after {MAX_RETRIES} attempts: {str(e)}", exc_info=True)
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

    try:
        # If not in cache or cache disabled, fetch from sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(TOKEN_FILE_PATH, scope)
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
        
    except Exception as e:
        cache_logger.error(f"Error fetching worksheet: {e}")
        raise