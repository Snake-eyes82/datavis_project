# In file_handlers/converters/xlsx.py

import pandas as pd
import io
import logging
# No need to import helper functions here if pandas handles date/amount conversion directly

# Get a logger instance for this module
logger = logging.getLogger(__name__)


# Updated xlsx_to_list_of_dicts function to handle Timestamp serialization and logging
def xlsx_to_list_of_dicts(xlsx_content: bytes):
    """
    Converts XLSX content (bytes) to a list of dictionaries.
    Assumes the first row is the header.
    Attempts to convert Timestamp objects to strings.
    Includes debug logging.
    """
    header_list = []
    list_of_dicts = []
    error_message = None

    # logger.debug(f"Debug in xlsx_to_list_of_dicts: Input type: {type(xlsx_content)}") # Keep minimized

    try:
        excel_file = io.BytesIO(xlsx_content)
        # Read the Excel file, keeping original data types where possible
        # Pandas handles date and number conversion well by default
        df = pd.read_excel(excel_file, sheet_name=0, header=0)

        header_list = df.columns.tolist()

        # Convert DataFrame to a list of dictionaries
        # Use .where(pd.notna, None) to replace NaN with None, which is JSON serializable
        list_of_dicts = df.where(pd.notna, None).to_dict('records')

        # --- Data Type Conversion Logic for XLSX (Handle Timestamps for JSON) ---
        # Iterate through the list of dictionaries and convert specific types for JSON serialization
        for row_dict in list_of_dicts:
            for key, value in row_dict.items():
                # Convert Pandas Timestamp objects to ISO 8601 strings for JSON compatibility
                if isinstance(value, pd.Timestamp):
                    try:
                        # Convert to ISO 8601 format string
                        row_dict[key] = value.isoformat()
                        # logger.debug(f"Debug in xlsx_to_list_of_dicts: Converted Timestamp for column '{key}' to string.") # Keep minimized
                    except Exception as e:
                        logger.debug(f"Debug in xlsx_to_list_of_dicts: Error converting Timestamp for column '{key}': {e}")
                        row_dict[key] = str(value) # Fallback to string conversion

                # Pandas usually handles numeric conversion well, so no need to explicitly convert 'Amount' here
                # If needed, you could add a check similar to other converters

        logger.debug(f"Debug in xlsx_to_list_of_dicts: Converted XLSX to {len(list_of_dicts)} rows with {len(header_list)} headers. Timestamp objects converted.")

    except Exception as e:
        error_message = f"Error processing XLSX file: {e}"
        logger.error(f"Debug in xlsx_to_list_of_dicts: {error_message}", exc_info=True)
        header_list = []
        list_of_dicts = []


    return header_list, list_of_dicts, error_message