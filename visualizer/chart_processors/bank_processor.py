# In visualizer/chart_processors/bank_processor.py

import logging
# Import necessary helpers from the utils file
from file_handlers.converters.utils import clean_and_parse_amount, clean_and_format_date, find_matching_header, find_numeric_header

logger = logging.getLogger(__name__)

# This function will contain the bank chart data processing logic
def process_bank_chart_data(data_list: list[dict], headers: list[str], selected_xaxis: str = None, selected_yaxis: str = None):
    """
    Processes data specifically for bank statement chart visualization.
    Returns: (chart_data_dict, error_message, label_col_name, amount_col_name, numeric_headers, label_headers)
    """
    logger.info("Using bank chart processor.")
    error_message = None

    # --- Bank-Specific Header Analysis and Categorization ---
    # Common bank numeric headers: Amount, Balance, Credit, Debit
    # Common bank label headers: Date, Transaction Type, Description, Payee
    bank_numeric_names = ['amount', 'balance', 'credit', 'debit'] # Names for Y-axis candidates
    bank_label_names = ['date', 'transaction type', 'description', 'payee'] # Names for X-axis candidates

    numeric_headers = []
    label_headers = []

    if headers:
        headers_lower = [h.lower() for h in headers]

        # Populate numeric headers based on bank-specific names
        for header in headers:
            if header.lower() in bank_numeric_names:
                numeric_headers.append(header)

        # Populate label headers based on bank-specific names
        for header in headers:
            if header.lower() in bank_label_names:
                label_headers.append(header)

        # For the X-axis dropdown in the bank case, you might want to exclude numeric headers
        # Let's stick to non-numeric labels for X-axis in bank charts unless specified
        # label_headers will already contain headers that matched bank_label_names
        # If you want ALL non-numeric headers (not just specific bank ones) in X-axis, you'd refine this.
        # For now, let's ensure Date is always an option for X-axis if present
        if find_matching_header(headers, ['date']) and 'Date' not in label_headers:
             # Add the original 'Date' header if it exists and wasn't added by name match
            date_header = find_matching_header(headers, ['date'])
            if date_header:
                label_headers.insert(0, date_header) # Add Date at the beginning

        # Remove duplicates from label_headers while preserving order
        label_headers = list(dict.fromkeys(label_headers))


    # --- Handle empty data/headers ---
    if not data_list or not headers:
        error_message = "No data or headers available for bank charting."
        return ({'labels': [], 'datasets': [{'label': 'Bank Data', 'data': []}]}, error_message, None, None, numeric_headers, label_headers)


    # --- Column Identification (Use selected if provided, else Auto-detect for Bank) ---
    label_col_name = selected_xaxis
    amount_col_name = selected_yaxis

    if not label_col_name or not amount_col_name:
        # Auto-detect default X-axis for Bank: Prioritize 'Date'
        label_col_name = find_matching_header(headers, ['date'])
        # If no Date, fallback to Description or first label header
        if not label_col_name:
            label_col_name = find_matching_header(headers, ['description', 'transaction type', 'payee'])
        if not label_col_name and label_headers:
            label_col_name = label_headers[0] # Fallback to first identified label header


        # Auto-detect default Y-axis for Bank: Prioritize 'Amount' or 'Balance'
        amount_col_name = find_matching_header(headers, ['amount', 'balance', 'credit', 'debit'])
        # If no specific bank numeric, fallback to first numeric header based on name
        if not amount_col_name and numeric_headers:
            amount_col_name = numeric_headers[0]


        # If fallback still didn't find both suitable columns
        if not label_col_name or not amount_col_name:
            error_message = "Could not identify suitable columns for bank charting (Label/Amount), even with fallback."
            return ({'labels': [], 'datasets': [{'label': 'Bank Data', 'data': []}]}, error_message, None, None, numeric_headers, label_headers)


    # --- Check if the determined columns actually exist in the headers ---
    if label_col_name not in headers:
        error_message = f"Determined Label column '{label_col_name}' not found in headers for bank type."
        return ({'labels': [], 'datasets': [{'label': 'Bank Data', 'data': []}]}, error_message, None, None, numeric_headers, label_headers)

    if amount_col_name not in headers:
        error_message = f"Determined Amount column '{amount_col_name}' not found in headers for bank type."
        return ({'labels': [], 'datasets': [{'label': 'Bank Data', 'data': []}]}, error_message, None, None, numeric_headers, label_headers)


    # --- Extract and Clean Data using Determined Columns (Bank) ---
    extracted_labels = []
    extracted_amounts = []

    for i, row_dict in enumerate(data_list):
        if not isinstance(row_dict, dict):
            if error_message is None: error_message = f"Data structure error: Expected list of dictionaries, found {type(row_dict)} in row {i+1}."
            continue

        raw_label_value = row_dict.get(label_col_name, None)
        raw_amount_value = row_dict.get(amount_col_name, None)

        # For bank data, the X-axis is often a Date, so use the date cleaner if applicable
        if label_col_name and label_col_name.lower() in bank_label_names and 'date' in label_col_name.lower():
            cleaned_label = clean_and_format_date(raw_label_value)
             # Decide how to handle date parsing failure for bank - maybe skip the row or use raw string?
            if cleaned_label is None:
                logger.warning(f"Processing row {i+1} in bank processing: Date parsing failure for column '{label_col_name}'. Using raw value or skipping.")
                 # Option 1: Skip the row if date is essential
                 # continue
                 # Option 2: Use raw string as label
                cleaned_label = str(raw_label_value) if raw_label_value is not None else ''


        else: # If label is not a date or bank label, treat as generic string label
            cleaned_label = str(raw_label_value) if raw_label_value is not None else ''


        # For bank data, the Y-axis should be numeric, use the amount cleaner
        cleaned_amount = clean_and_parse_amount(raw_amount_value)

        # Only add if cleaned amount is valid
        if cleaned_amount is not None:
             # If date cleaning was required AND it succeeded, OR if date cleaning was not required
            if not (label_col_name and label_col_name.lower() in bank_label_names and 'date' in label_col_name.lower() and cleaned_label is None):
                extracted_labels.append(cleaned_label)
                extracted_amounts.append(cleaned_amount)
             # else: # Log if skipped due to date cleaning failure (handled above if skipping)
                 # pass


    labels = extracted_labels
    amounts = extracted_amounts

    if not labels or not amounts:
        if error_message is None:
            error_message = "No valid data points extracted using the selected columns for bank type."


    chart_js_data = {
        'labels': labels,
        'datasets': [{
            'label': amount_col_name if amount_col_name else 'Bank Data',
            'data': amounts,
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1,
            'fill': False
        }]
    }

    # Return 6 values for the dispatcher
    return (chart_js_data, error_message, label_col_name, amount_col_name, numeric_headers, label_headers)