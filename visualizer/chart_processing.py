# In visualizer/chart_processing.py

import logging
# Import helper functions from the file_handlers app (used by processors)
from file_handlers.converters.utils import clean_and_format_date, clean_and_parse_amount, find_matching_header, find_numeric_header

# Import the type-specific chart processor modules (importing the modules)
from .chart_processors import generic_processor
from .chart_processors import stock_processor
from .chart_processors import bank_processor
# Add imports for other processor modules here

logger = logging.getLogger(__name__)

# --- Function to infer data type based on headers ---
def infer_data_type(headers: list[str]) -> str:
    """
    Infers the data type (e.g., 'stock', 'bank', 'generic', 'unknown') based on header names.
    Returns a string representing the inferred type.
    """
    if not headers:
        return 'unknown'

    headers_lower = [h.lower() for h in headers]

    stock_headers_indicators = {'date', 'open', 'high', 'low', 'close', 'volume', 'adjusted', 'return', 'ticker'}
    bank_headers_indicators = {'date', 'transaction type', 'amount', 'balance', 'description', 'payee', 'withdrawal', 'deposit'}

    # Count how many indicator headers are present for each type
    stock_score = sum(1 for header in headers_lower if header in stock_headers_indicators)
    bank_score = sum(1 for header in headers_lower if header in bank_headers_indicators)

    # Define thresholds for inference
    stock_threshold = 4 # Requires at least 4 common stock headers
    bank_threshold = 3  # Requires at least 3 common bank headers

    if stock_score >= stock_threshold and stock_score > bank_score:
        return 'stock'
    elif bank_score >= bank_threshold and bank_score > stock_score:
        return 'bank'
    # You might add more elif conditions here for other types

    # Default to 'generic' if no specific type is strongly matched
    return 'generic'


# --- Main prepare_chart_data function (Dispatcher) ---
def prepare_chart_data(data_list: list[dict], headers: list[str], selected_xaxis: str = None, selected_yaxis: str = None):
    """
    Infers data type and dispatches data preparation to the appropriate processor.
    Returns a tuple: (chart_data_dict, error_message_or_None, label_col_name_used, amount_col_name_used, numeric_headers, label_headers, inferred_data_type).
    """
    # Infer the data type
    data_type = infer_data_type(headers)
    logger.info(f"Inferred data type: {data_type}")

    # --- Dispatch to the appropriate type-specific processor function ---
    # The processor functions are expected to return 6 values:
    # (chart_data_dict, error_message, label_col_name, amount_col_name, numeric_headers, label_headers)
    try:
        if data_type == 'stock':
            chart_data, error_message, label_col_name, amount_col_name, numeric_headers, label_headers = stock_processor.process_stock_chart_data(
                data_list, headers, selected_xaxis, selected_yaxis
            )
        elif data_type == 'bank':
             chart_data, error_message, label_col_name, amount_col_name, numeric_headers, label_headers = bank_processor.process_bank_chart_data(
                data_list, headers, selected_xaxis, selected_yaxis
             )
        # Add more elif conditions for other types here
        elif data_type == 'generic':
            chart_data, error_message, label_col_name, amount_col_name, numeric_headers, label_headers = generic_processor.process_generic_chart_data(
                data_list, headers, selected_xaxis, selected_yaxis
             )
        else: # Handle 'unknown' type - fallback to generic processing
            logger.warning(f"Unknown or unhandled data type inferred: {data_type}. Falling back to generic processing.")
            chart_data, error_message, label_col_name, amount_col_name, numeric_headers, label_headers = generic_processor.process_generic_chart_data(
                data_list, headers, selected_xaxis, selected_yaxis
             )
            # You might add an error message here if 'unknown' shouldn't fall back
            if error_message is None: # If generic didn't set an error, add one for unknown type
                error_message = f"Could not process data for unknown type: {data_type}"

    except Exception as e:
         # Catch any unexpected errors that occur within the processor functions
        logger.error(f"An unexpected error occurred during {data_type} chart processing: {e}", exc_info=True)
        chart_data = {'labels': [], 'datasets': [{'label': 'Error', 'data': []}]}
        error_message = f"An error occurred during chart processing ({data_type} type): {e}"
        label_col_name = None
        amount_col_name = None
        numeric_headers = []
        label_headers = []


    # Return the results from the type-specific processor + the inferred data type
    return (chart_data, error_message, label_col_name, amount_col_name, numeric_headers, label_headers, data_type) # Return 7 values