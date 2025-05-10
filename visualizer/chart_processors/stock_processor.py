# In visualizer/chart_processors/stock_processor.py

import logging
# Import necessary helpers from the utils file
from file_handlers.converters.utils import clean_and_parse_amount, clean_and_format_date, find_matching_header, find_numeric_header

logger = logging.getLogger(__name__)

# This function will contain the stock chart data processing logic
def process_stock_chart_data(data_list: list[dict], headers: list[str], selected_xaxis: str = None, selected_yaxis: str = None):
    """
    Processes data specifically for stock chart visualization.
    Returns: (chart_data_dict, error_message, label_col_name, amount_col_name, numeric_headers, label_headers)
    """
    logger.info("Using stock chart processor.")
    error_message = None

    # --- Stock-Specific Header Analysis and Categorization ---
    # For stock data, we need to be more specific about numeric and label headers.
    # Common stock numeric headers: Open, High, Low, Close, Volume, Adjusted, Return
    # Common stock label headers: Date, Ticker, Name
    stock_numeric_names = ['open', 'high', 'low', 'close', 'volume', 'adjusted', 'return'] # Names for Y-axis candidates
    stock_label_names = ['date', 'ticker', 'name'] # Names for X-axis candidates

    numeric_headers = []
    label_headers = []

    if headers:
        headers_lower = [h.lower() for h in headers]

        # Populate numeric headers based on stock-specific names
        for header in headers:
            if header.lower() in stock_numeric_names:
                numeric_headers.append(header)

        # Populate label headers based on stock-specific names
        for header in headers:
            if header.lower() in stock_label_names:
                label_headers.append(header)

        # For the X-axis dropdown in the stock case, it's often useful to include Date,
        # and sometimes even numeric like Adjusted Close for comparative charts.
        # For now, let's include all headers as label candidates for flexibility,
        # but you might refine this later.
        label_headers = list(headers) # Include all for X-axis flexibility initially

    # --- Handle empty data/headers ---
    if not data_list or not headers:
        error_message = "No data or headers available for stock charting."
        return ({'labels': [], 'datasets': [{'label': 'Stock Data', 'data': []}]}, error_message, None, None, numeric_headers, label_headers)


    # --- Column Identification (Use selected if provided, else Auto-detect for Stock) ---
    label_col_name = selected_xaxis
    amount_col_name = selected_yaxis

    if not label_col_name or not amount_col_name:
        # Auto-detect default X-axis for Stock: Prioritize 'Date'
        label_col_name = find_matching_header(headers, ['date'])
        # If no Date, maybe fallback to Ticker or first label header
        if not label_col_name:
            label_col_name = find_matching_header(headers, ['ticker', 'name'])
        if not label_col_name and label_headers:
            label_col_name = label_headers[0] # Fallback to first identified label header


        # Auto-detect default Y-axis for Stock: Prioritize common stock metrics (e.g., Adjusted, Close)
        amount_col_name = find_matching_header(headers, ['adjusted', 'close', 'open', 'high', 'low', 'volume'])
        # If no specific stock numeric, fallback to first numeric header based on name
        if not amount_col_name and numeric_headers:
            amount_col_name = numeric_headers[0]


        # If fallback still didn't find both suitable columns
        if not label_col_name or not amount_col_name:
            error_message = "Could not identify suitable columns for stock charting (Label/Amount), even with fallback."
            return ({'labels': [], 'datasets': [{'label': 'Stock Data', 'data': []}]}, error_message, None, None, numeric_headers, label_headers)


    # --- Check if the determined columns actually exist in the headers ---
    if label_col_name not in headers:
        error_message = f"Determined Label column '{label_col_name}' not found in headers for stock type."
        return ({'labels': [], 'datasets': [{'label': 'Stock Data', 'data': []}]}, error_message, None, None, numeric_headers, label_headers)

    if amount_col_name not in headers:
        error_message = f"Determined Amount column '{amount_col_name}' not found in headers for stock type."
        return ({'labels': [], 'datasets': [{'label': 'Stock Data', 'data': []}]}, error_message, None, None, numeric_headers, label_headers)


    # --- Extract and Clean Data using Determined Columns (Stock) ---
    extracted_labels = []
    extracted_amounts = []

    for i, row_dict in enumerate(data_list):
        if not isinstance(row_dict, dict):
            if error_message is None: error_message = f"Data structure error: Expected list of dictionaries, found {type(row_dict)} in row {i+1}."
            continue

        raw_label_value = row_dict.get(label_col_name, None)
        raw_amount_value = row_dict.get(amount_col_name, None)

        # For stock data, the X-axis is often a Date, so use the date cleaner if applicable
        if label_col_name and label_col_name.lower() in stock_label_names and 'date' in label_col_name.lower():
            cleaned_label = clean_and_format_date(raw_label_value)
             # Decide how to handle date parsing failure for stock - maybe skip the row?
            if cleaned_label is None:
                logger.warning(f"Skipping row {i+1} in stock processing due to date parsing failure for column '{label_col_name}'. Raw Value='{raw_label_value}'")
                continue # Skip row if date cannot be parsed as requested

        else: # If label is not a date or stock label, treat as generic string label
            cleaned_label = str(raw_label_value) if raw_label_value is not None else ''


        # For stock data, the Y-axis should be numeric, use the amount cleaner
        cleaned_amount = clean_and_parse_amount(raw_amount_value)

        # Only add if both label (if date cleaning was required and succeeded) and cleaned amount are valid
        if cleaned_amount is not None:
             # If date cleaning was not required OR date cleaning was required and succeeded (cleaned_label is not None)
            if not (label_col_name and label_col_name.lower() in stock_label_names and 'date' in label_col_name.lower()) or (cleaned_label is not None):
                extracted_labels.append(cleaned_label)
                extracted_amounts.append(cleaned_amount)
            # else: # Log if skipped due to date cleaning failure (handled above)
                # pass


    labels = extracted_labels
    amounts = extracted_amounts

    if not labels or not amounts:
        if error_message is None:
            error_message = "No valid data points extracted using the selected columns for stock type."


    chart_js_data = {
        'labels': labels,
        'datasets': [{
            'label': amount_col_name if amount_col_name else 'Stock Data',
            'data': amounts,
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1,
            'fill': False
        }]
    }

    # Return 6 values for the dispatcher
    return (chart_js_data, error_message, label_col_name, amount_col_name, numeric_headers, label_headers)