# In file_handlers/converters/csv.py

import csv
import io
import logging

# Import helper functions from the utils module
from .utils import clean_and_parse_amount # csv_to_list_of_dicts only uses clean_and_parse_amount

# Get a logger instance for this module
logger = logging.getLogger(__name__)


# CSV converter function implementation
# It still needs to handle the 'Amount' conversion to float.
# Ensure the header detection is simple, assuming the first row of the CSV it receives is the header.
def csv_to_list_of_dicts(csv_file_object):
    """
    Converts CSV content from a file-like object into a list of dictionaries.
    Assumes the first row is the header.
    Attempts to convert 'Amount' column to float.
    Includes debug logging.

    Args:
        csv_file_object: A file-like object containing CSV data (e.g., result of open(), io.StringIO).

    Returns:
        A tuple containing:
        - header_list (list): List of column headers.
        - list_of_dicts (list): List of dictionaries, each representing a row.
        - error_message (str or None): An error message if conversion failed.
    """
    header_list = []
    list_of_dicts = []
    error_message = None

    # logger.debug(f"Debug in csv_to_list_of_dicts: Input type: {type(csv_file_object)}") # Keep minimized

    try:
        csv_reader = csv.reader(csv_file_object)

        # Read the header row (assuming the first row is the header now)
        try:
            header_row = None
            for row in csv_reader:
                if any(cell.strip() for cell in row):
                    header_row = row
                    break # Found the first non-empty row, assume it's the header

            if header_row is None:
                error_message = "CSV file is empty or contains only empty rows."
                logger.debug(f"Debug in csv_to_list_of_dicts: {error_message}")
                return [], [], error_message


            header_list = [header.strip() for header in header_row] # Strip whitespace from headers
            logger.debug(f"Debug in csv_to_list_of_dicts: Identified {len(header_list)} headers.")

        except Exception as e:
            error_message = f"Error reading header row from CSV: {e}"
            logger.error(f"Debug in csv_to_list_of_dicts: {error_message}", exc_info=True)
            return [], [], error_message


        # Process data rows
        for row in csv_reader:
            if not any(cell.strip() for cell in row):
                continue

            row_dict = {}
            padded_row = row + [None] * (len(header_list) - len(row))

            for i, header_name in enumerate(header_list):
                if not header_name:
                    continue

                cell_value = padded_row[i]

                # --- Data Type Conversion Logic ---
                if isinstance(header_name, str) and header_name.lower() == 'amount':
                    try:
                        # Use the helper function for amount parsing
                        amount_value = clean_and_parse_amount(cell_value)
                        row_dict[header_name] = amount_value

                    except (ValueError, TypeError) as e:
                        # logger.debug(f"Debug in csv_to_list_of_dicts: Could not convert Amount value '{cell_value}' to float for column '{headerName}': {e}") # Keep minimized
                        row_dict[header_name] = None # Set to None if conversion fails

                else:
                    row_dict[header_name] = cell_value

            if row_dict and any(row_dict.values()):
                list_of_dicts.append(row_dict)


        if not list_of_dicts:
            error_message = error_message if error_message else "No data rows found in CSV."
            logger.debug(f"Debug in csv_to_list_of_dicts: {error_message}")
        elif not header_list:
            error_message = error_message if error_message else "No header row found in CSV."
            logger.debug(f"Debug in csv_to_list_of_dicts: {error_message}")


    except Exception as e:
        error_message = f"An error occurred during CSV processing: {e}"
        logger.error(f"Debug in csv_to_list_of_dicts: {error_message}", exc_info=True)
        header_list = []
        list_of_dicts = []


    return header_list, list_of_dicts, error_message