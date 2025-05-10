# In visualizer/chart_processors/generic_processor.py

import logging
# Import necessary helpers from the utils file
from file_handlers.converters.utils import clean_and_parse_amount, clean_and_format_date, find_matching_header, find_numeric_header

logger = logging.getLogger(__name__)

# This function will contain the generic chart data processing logic
def process_generic_chart_data(data_list: list[dict], headers: list[str], selected_xaxis: str = None, selected_yaxis: str = None):
    """
    Processes data for generic chart visualization.
    Returns: (chart_data_dict, error_message, label_col_name, amount_col_name, numeric_headers, label_headers)
    """
    logger.info("Using generic chart processor.")

    labels = []
    amounts = []
    error_message = None

    numeric_headers = []
    label_headers = [] # Initialize label_headers

    # --- Analyze Headers and Categorize (Strictly Name-Based for Generic) ---
    common_numeric_names = ['amount', 'value', 'price', 'volume', 'count', 'score', 'change', 'open', 'high', 'low', 'close']

    if headers:
        for header in headers:
            header_lower = header.lower()
            is_numeric_by_name = any(name in header_lower for name in common_numeric_names)
            if is_numeric_by_name:
                numeric_headers.append(header)
            else:
                label_headers.append(header)

        # For the X-axis dropdown in the generic case, include ALL original headers for maximum flexibility.
        # If you want to exclude numeric headers from X-axis for generic, remove this line.
        label_headers = list(headers)


    # --- Handle empty data/headers ---
    if not data_list or not headers:
        error_message = "No data or headers available for charting."
        return ({'labels': [], 'datasets': [{'label': 'Data', 'data': []}]}, error_message, None, None, numeric_headers, label_headers)


    # --- Column Identification (Use selected if provided, else auto-detect for Generic) ---
    label_col_name = selected_xaxis
    amount_col_name = selected_yaxis

    if not label_col_name or not amount_col_name:
        # Default X-axis for Generic: First header from label_headers (which is all headers)
        label_col_name = label_headers[0] if label_headers else None
        # Default Y-axis for Generic: First header from numeric_headers
        amount_col_name = numeric_headers[0] if numeric_headers else None

        if not label_col_name or not amount_col_name:
            error_message = "Could not identify suitable columns for charting (Label/Amount) for generic type, even with fallback."
            return ({'labels': [], 'datasets': [{'label': 'Data', 'data': []}]}, error_message, None, None, numeric_headers, label_headers)


    # --- Check if the determined columns actually exist in the headers ---
    if label_col_name not in headers:
        error_message = f"Determined Label column '{label_col_name}' not found in headers for generic type."
        return ({'labels': [], 'datasets': [{'label': 'Data', 'data': []}]}, error_message, None, None, numeric_headers, label_headers)

    if amount_col_name not in headers:
        error_message = f"Determined Amount column '{amount_col_name}' not found in headers for generic type."
        return ({'labels': [], 'datasets': [{'label': 'Data', 'data': []}]}, error_message, None, None, numeric_headers, label_headers)


    # --- Extract and Clean Data using Determined Columns (Generic) ---
    extracted_labels = []
    extracted_amounts = []

    for i, row_dict in enumerate(data_list):
        if not isinstance(row_dict, dict):
            if error_message is None: error_message = f"Data structure error: Expected list of dictionaries, found {type(row_dict)} in row {i+1}."
            continue

        raw_label_value = row_dict.get(label_col_name, None)
        raw_amount_value = row_dict.get(amount_col_name, None)

        cleaned_label = str(raw_label_value) if raw_label_value is not None else ''
        # Optional: Use clean_and_format_date here if the selected label column is likely a date
        # if label_col_name and label_col_name.lower() == 'date': # Basic check, could be more sophisticated
        #     cleaned_label = clean_and_format_date(raw_label_value)
        #     if cleaned_label is None:
        #          # Decide how to handle date parsing failure in generic case
        #          cleaned_label = str(raw_label_value) if raw_label_value is not None else '' # Fallback to string


        cleaned_amount = clean_and_parse_amount(raw_amount_value)

        if cleaned_amount is not None:
            extracted_labels.append(cleaned_label)
            extracted_amounts.append(cleaned_amount)


    labels = extracted_labels
    amounts = extracted_amounts

    if not labels or not amounts:
        if error_message is None:
            error_message = "No valid data points extracted using the selected columns for generic type."


    chart_js_data = {
        'labels': labels,
        'datasets': [{
            'label': amount_col_name if amount_col_name else 'Data',
            'data': amounts,
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1,
            'fill': False
        }]
    }

    # Return 6 values for the dispatcher
    return (chart_js_data, error_message, label_col_name, amount_col_name, numeric_headers, label_headers)