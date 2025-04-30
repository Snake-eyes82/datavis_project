# In file_handlers/utils.py

import datetime
import pandas as pd
import logging

# Get a logger instance for this module
logger = logging.getLogger(__name__)


def clean_and_format_date(raw_date):
    """
    Cleans and formats a raw date value into a consistent string
    (e.g., ISO 8601 'YYYY-MM-DD') or returns None if invalid.
    Handles datetime objects, numbers (Excel dates), and strings.
    Includes debug logging.
    """
    logger.debug(f"Debug in clean_and_format_date: Cleaning raw date: {raw_date} (Type: {type(raw_date)})")
    if isinstance(raw_date, datetime.datetime): # Use datetime.datetime
        return raw_date.date().isoformat() # Return only the date part as ISO 8601
    elif isinstance(raw_date, (int, float)):
        try:
            # Using pandas to_datetime can be more robust for various number/string formats
            # Attempt conversion using pandas, which handles Excel date numbers too
            # Excel's date origin for Windows is 1899-12-30
            date_obj = pd.to_datetime(raw_date, origin='1899-12-30', unit='D', errors='coerce')
            if pd.isna(date_obj):
                logger.debug(f"Debug in clean_and_format_date: Could not convert numeric date {raw_date} using pandas.")
                return None
            return date_obj.date().isoformat() # Return just the date part as ISO format

        except Exception as e:
            logger.debug(f"Debug in clean_and_format_date: Could not convert numeric date {raw_date} using pandas: {e}")
            return None
    elif isinstance(raw_date, str):
        raw_date = raw_date.strip()
        if not raw_date:
            logger.debug("Debug in clean_and_format_date: Empty date string.")
            return None
        try:
            # Using pandas to_datetime is more flexible here too
            date_obj = pd.to_datetime(raw_date, errors='coerce') # Use errors='coerce' to return NaT for invalid parsing
            if pd.isna(date_obj): # Check if pandas failed to parse (result is NaT)
                logger.debug(f"Debug in clean_and_format_date: Could not parse date string '{raw_date}' using pandas.")
                return None
            return date_obj.date().isoformat() # Return just the date part as ISO format

        except Exception as e:
            logger.debug(f"Debug in clean_and_format_date: Unexpected error parsing date string '{raw_date}' with pandas: {e}")
            return None
    else:
        # Handle None or other types
        if raw_date is not None:
            logger.debug(f"Debug in clean_and_format_date: Unhandled date type: {type(raw_date)} for value {raw_date}")
        return None # Or handle appropriately


def clean_and_parse_amount(raw_amount):
    """
    Cleans and parses a raw amount value into a float or returns None if invalid.
    Handles numbers and strings with currency symbols, commas, etc.
    Includes debug logging.
    """
    logger.debug(f"Debug in clean_and_parse_amount: Cleaning raw amount: {raw_amount} (Type: {type(raw_amount)})")
    if isinstance(raw_amount, (int, float)):
        return float(raw_amount)
    elif isinstance(raw_amount, str):
        raw_amount = raw_amount.strip()
        if not raw_amount:
            logger.debug("Debug in clean_and_parse_amount: Empty amount string.")
            return None
        # Remove currency symbols, commas, etc.
        cleaned_amount_str = raw_amount.replace('$', '').replace('€', '').replace('£', '').replace(',', '').strip()
        try:
            # Handle potential parentheses for negative numbers (common in accounting)
            if cleaned_amount_str.startswith('(') and cleaned_amount_str.endswith(')'):
                cleaned_amount_str = '-' + cleaned_amount_str[1:-1]
            return float(cleaned_amount_str)
        except ValueError:
            logger.debug(f"Debug in clean_and_parse_amount: Could not parse amount string: {raw_amount}")
            return None
        except Exception as e:
            logger.debug(f"Debug in clean_and_parse_amount: Unexpected error parsing amount string '{raw_amount}': {e}")
            return None
    else:
        # Handle None or other types
        if raw_amount is not None:
            logger.debug(f"Debug in clean_and_parse_amount: Unhandled amount type: {type(raw_amount)} for value {raw_amount}")
        return None