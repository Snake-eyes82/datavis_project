# In file_handlers/converters/ods.py
print("--- Loading ods.py ---") # Add this as the very first line

import sys
import os
import io # Make sure io is imported here too

print("--- Debugging Environment ---")
print(f"Current working directory: {os.getcwd()}")
print(f"Python Executable: {sys.executable}")
print("Sys Path:")
for path in sys.path:
    print(f"- {path}")
print("---------------------------")

# --- Necessary imports start here ---
#from file_handlers.converters.ods import ods_to_list_of_dicts
import file_handlers.converters.ods_handler as ods_handler
import pyexcel
import logging
import datetime # Needed for isinstance check in ods_to_list_of_dicts if you're using it there
from odfpy import opendoc

# Import helper functions from the utils module
from .utils import clean_and_format_date, clean_and_parse_amount

# Get a logger instance for this module (assuming this is done below imports)
logger = logging.getLogger(__name__)

def test_odfpy_read(raw_file_content: bytes):
    """
    Tests reading ODS file content directly using odfpy.
    """
    logger.debug("Debug in test_odfpy_read: Starting direct read test with odfpy.")
    try:
        # Use io.BytesIO to wrap the bytes content for odfpy
        file_like_object = io.BytesIO(raw_file_content)
        doc = opendoc.OpenDocument(file_like_object)
        # If no exception is raised by OpenDocument, it means odfpy could open the file
        logger.debug("Debug in test_odfpy_read: Successfully opened ODS file directly with odfpy.")
        # You could add more checks here, e.g., accessing sheets or cells
        body = doc.text()
        logger.debug(f"Debug in test_odfpy_read: Successfully accessed document body with odfpy (partial read test).")

        return True, None # Success

    except Exception as e:
        logger.error(f"Debug in test_odfpy_read: Failed to read ODS file directly with odfpy: {e}", exc_info=True)
        return False, str(e) # Failure

# ODS converter function implementation
def ods_to_list_of_dicts(raw_file_content: bytes):
    """
    Parses ODS file content and returns data as a list of dictionaries.
    Includes extensive debug logging to diagnose issues.
    """
    logger.debug("Debug in ods_to_list_of_dicts: Starting ODS parsing.")

    header_list = []
    list_of_dicts = []
    error_message = None

    try:
        # Use pyexcel to get the book from the raw byte content
        # CORRECTED: Added file_type='.ods' argument
        logger.debug("Debug in ods_to_list_of_dicts: Calling pyexcel.get_book with file_type='.ods'.")
        book = pyexcel.get_book(file_content=raw_file_content, file_type='ods', library='pyexcel-ods3')

        logger.debug("Debug in ods_to_list_of_dicts: Got book object.")
        # Access sheets using the correct method .sheets()
        logger.debug(f"Debug in ods_to_list_of_dicts: Number of sheets: {len(book.sheets())}")
        logger.debug(f"Debug in ods_to_list_of_dicts: Sheet names: {book.sheet_names()}")

        # Check if there are any sheets using the correct method .sheets()
        if not book.sheets():
            error_message = "ODS file contains no sheets."
            logger.debug(f"Debug in ods_to_list_of_dicts: {error_message}")
            return header_list, list_of_dicts, error_message

        # Assuming data is in the first sheet (index 0)
        sheet = book.sheet_by_index(0)
        logger.debug(f"Debug in ods_to_list_of_dicts: Selected first sheet: '{sheet.name}'")

        # Get data as list of lists using the correct method .to_array()
        data_as_lists = sheet.to_array()
        logger.debug(f"Debug in ods_to_list_of_dicts: Got data as list of lists. Total rows (including potential header): {len(data_as_lists)}")

        if len(data_as_lists) > 0:
            # Log the first few raw rows from pyexcel to inspect structure and data types
            logger.debug(f"Debug in ods_to_list_of_dicts: First 5 raw rows from sheet.to_array(): {data_as_lists[:5]}")
        else:
            logger.debug("Debug in ods_to_list_of_dicts: data_as_lists is empty after sheet.to_array().")

        if not data_as_lists:
            error_message = "ODS sheet is empty."
            logger.debug(f"Debug in ods_to_list_of_dicts: {error_message}")
            return header_list, list_of_dicts, error_message

        # Check if data_as_lists has at least one row for the header
        if len(data_as_lists) < 1:
            error_message = "ODS sheet contains no rows (expected at least a header row)."
            logger.debug(f"Debug in ods_to_list_of_dicts: {error_message}")
            return header_list, list_of_dicts, error_message

        # Assume the first row is headers
        raw_headers = data_as_lists[0]
        data_rows = data_as_lists[1:] # Data starts from the second row


        # Clean headers and create a mapping to lowercase for easier lookup
        header_list = [str(h).strip() if h is not None else '' for h in raw_headers]
        # Create a mapping from cleaned lowercase header name to its original index
        header_map = {h.lower(): i for i, h in enumerate(header_list) if h}

        logger.debug(f"Debug in ods_to_list_of_dicts: Processed headers: {header_list}")
        logger.debug(f"Debug in ods_to_list_of_dicts: Header map (lowercase -> index): {header_map}")


        # --- Standardize data into list of dictionaries ---
        # Identify column indices for 'Date' and 'Amount' (case-insensitive lookup)
        # Adjust these lookup keys if your ODS file headers use different words (e.g., 'transaction date', 'value')
        # Ensure the dictionary keys created ('Date', 'Amount') match what your JS expects!
        date_col_index = header_map.get('date', -1) # Look for 'date'
        amount_col_index = header_map.get('amount', -1) # Look for 'amount'

        # Add checks for alternative common headers if needed (adjust based on your file's likely headers)
        if date_col_index == -1:
            date_col_index = header_map.get('posting date', -1) # Also look for 'posting date'
        if date_col_index == -1:
            date_col_index = header_map.get('transaction date', -1) # Also look for 'transaction date'

        if amount_col_index == -1:
            amount_col_index = header_map.get('value', -1) # Also look for 'value'
        if amount_col_index == -1:
            amount_col_index = header_map.get('credit', -1) # Also look for 'credit'
        if amount_col_index == -1:
            amount_col_index = header_map.get('debit', -1) # Also look for 'debit'


        logger.debug(f"Debug in ods_to_list_of_dicts: Determined column indices - Date: {date_col_index}, Amount: {amount_col_index}")

        if date_col_index == -1 or amount_col_index == -1:
            error_message = "Could not find required 'Date' or 'Amount' columns in the ODS file based on common headers. Please check your ODS file headers."
            logger.debug(f"Debug in ods_to_list_of_dicts: {error_message}")
            # Ensure header_list and list_of_dicts are empty before returning on this specific error
            header_list = []
            list_of_dicts = []
            return header_list, list_of_dicts, error_message


        # Determine the maximum index needed to avoid IndexError when accessing row data
        max_index = max(date_col_index, amount_col_index)
        logger.debug(f"Debug in ods_to_list_of_dicts: Maximum column index needed for data extraction: {max_index}")
        logger.debug(f"Debug in ods_to_list_of_dicts: Processing {len(data_rows)} data rows...")


        # Iterate over the data rows and create dictionaries
        for i, row in enumerate(data_rows):
            # Add a check to skip empty rows
            # Ensure the row has enough columns before accessing indices
            if len(row) > max_index and any(cell for cell in row): # Skip if the row is entirely empty or None values AND has enough columns
                # Extract raw values using the identified column indices
                raw_date = row[date_col_index]
                raw_amount = row[amount_col_index]

                # Use your existing or new helper functions to clean and parse
                # Log types before cleaning to help diagnose parsing issues
                logger.debug(f"Debug in ods_to_list_of_dicts: Processing Row {i+2} - Raw Date: '{raw_date}' (Type: {type(raw_date)}), Raw Amount: '{raw_amount}' (Type: {type(raw_amount)})")
                cleaned_date = clean_and_format_date(raw_date) # Call your helper function
                cleaned_amount = clean_and_parse_amount(raw_amount) # Call your helper function
                logger.debug(f"Debug in ods_to_list_of_dicts: Row {i+2} - Cleaned Date: '{cleaned_date}', Cleaned Amount: {cleaned_amount}")


                # Only add the row if key data (Date and Amount) was successfully parsed by the helper functions
                if cleaned_date is not None and cleaned_amount is not None:
                    # Create a dictionary for the row with standardized keys
                    # Make sure 'Date' and 'Amount' match the keys expected by your frontend JS (in chart_only.html and visualizer_interface.html)
                    row_dict = {
                        'Date': cleaned_date, # Standardized key for Date
                        'Amount': cleaned_amount, # Standardized key for Amount
                        # You can add other fields here if needed...
                    }
                    list_of_dicts.append(row_dict)
                else:
                    # More detailed skipping message
                    logger.debug(f"Debug in ods_to_list_of_dicts: Skipping row {i+2} due to failed date or amount parsing. Raw Date='{raw_date}', Raw Amount='{raw_amount}', Cleaned Date='{cleaned_date}', Cleaned Amount='{cleaned_amount}'")


            else:
                # More detailed skipping message (handles both insufficient columns and empty rows)
                 if not any(cell for cell in row):
                      logger.debug(f"Debug in ods_to_list_of_dicts: Skipping row {i+2} as it appears empty.")
                 else:
                      logger.debug(f"Debug in ods_to_list_of_dicts: Skipping row {i+2} due to insufficient columns (Row length: {len(row)}, Max expected index: {max_index}).")


        logger.debug(f"Debug in ods_to_list_of_dicts: Finished processing data rows.")
        logger.debug(f"Debug in ods_to_list_of_dicts: Final list_of_dicts size: {len(list_of_dicts)}")
        # Uncomment the line below to see the first few dictionaries extracted
        # logger.debug(f"Debug in ods_to_list_of_dicts: Final list_of_dicts content (first 5 rows): {list_of_dicts[:5]}")


    # Capture the exception and include its string representation in the error message
    except Exception as e:
        # This line formats the error message and includes the traceback due to exc_info=True
        error_message = f"An unexpected error occurred during ODS processing: {e}"
        logger.error(f"Debug in ods_to_list_of_dicts: {error_message}", exc_info=True)
        # Ensure header_list and list_of_dicts are empty on error
        header_list = []
        list_of_dicts = []
        return header_list, list_of_dicts, error_message

    # Return the results if no exception occurred
    return header_list, list_of_dicts, error_message