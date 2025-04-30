# In file_handlers/converters/xml.py

import xml.etree.ElementTree as ET
import json
import io
import csv
import re
import logging

# Import helper functions from the utils module
from .utils import clean_and_format_date, clean_and_parse_amount

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# Define the namespaces used in the SpreadsheetML XML
SS_NAMESPACE = "urn:schemas-microsoft-com:office:spreadsheet"
HTML_NAMESPACE = "http://www.w3.org/TR/REC-html40"
namespaces = {
    'ss': SS_NAMESPACE,
    'html': HTML_NAMESPACE,
    'o': "urn:schemas-microsoft-com:office:office",
    'x': "urn:schemas-microsoft-com:office:excel",
}

# Define the expected header names for the SpreadsheetML format
EXPECTED_SPREADSHEETML_HEADERS = ["Posting date", "Description", "Type", "Amount", "Reconcile"]


def xml_to_csv_spreadsheetml(xml_content: bytes) -> str:
    """
    Converts SpreadsheetML XML content to CSV format, searching for the header row
    based on keywords and then extracting data rows.
    Includes debug logging to track progress.

    Args:
        xml_content: The raw byte content of the SpreadsheetML XML file.

    Returns:
        A string containing the data in CSV format.
        Returns an empty string on error or if the expected structure is not found.
    """
    csv_output = io.StringIO()
    csv_writer = csv.writer(csv_output)

    header_list = []
    data_rows = []
    header_row_index = None # To store the index of the row containing headers

    try:
        # Attempt to parse the XML
        root = ET.fromstring(xml_content)
        logger.debug("Debug in xml_to_csv_spreadsheetml: Successfully parsed XML.")


        # Check if this looks like SpreadsheetML XML
        worksheet = root.find('.//ss:Worksheet', namespaces)
        if worksheet is None:
            # This doesn't look like SpreadsheetML, return empty string for this function
            logger.debug("Debug in xml_to_csv_spreadsheetml: Input does not appear to be SpreadsheetML XML.")
            return ""

        table = worksheet.find('.//ss:Table', namespaces)
        if table is None:
            logger.debug("Debug in xml_to_csv_spreadsheetml: No Table found in SpreadsheetML.")
            return ""

        # Get all rows first to be able to check indices
        rows = table.findall('.//ss:Row', namespaces)
        logger.debug(f"Debug in xml_to_csv_spreadsheetml: Found {len(rows)} rows in SpreadsheetML.")

        # --- Phase 1: Find the header row ---
        # Iterate through initial rows to find the header based on keywords
        max_rows_to_check_for_header = 10
        logger.debug(f"Debug in xml_to_csv_spreadsheetml: Searching for header in first {min(len(rows), max_rows_to_check_for_header)} rows...")
        for i in range(min(len(rows), max_rows_to_check_for_header)):
            row = rows[i]
            row_values = []
            current_cell_index = 1

            # Extract cell values for the current row being checked for header
            for cell in row.findall('.//ss:Cell', namespaces):
                index_attr = cell.get(f'{{{SS_NAMESPACE}}}Index')
                if index_attr:
                    cell_index = int(index_attr)
                    while current_cell_index < cell_index:
                        row_values.append("")
                        current_cell_index += 1
                    current_cell_index = cell_index

                data_element = cell.find('.//ss:Data', namespaces)
                cell_value = ""
                if data_element is not None:
                    cell_value = ''.join(data_element.itertext()).strip() # Strip whitespace

                row_values.append(cell_value)
                current_cell_index += 1

            # Check if this row contains enough of the expected header keywords
            found_header_keywords = 0
            row_string_lower = " ".join(str(v).lower() for v in row_values if v is not None) # Combine row values into a single lowercase string

            for expected_header in EXPECTED_SPREADSHEETML_HEADERS:
                # Use regex word boundaries to match whole words, not substrings within words
                if re.search(r'\b' + re.escape(expected_header.lower()) + r'\b', row_string_lower):
                    found_header_keywords += 1

            # We'll consider it the header row if at least 3 of the expected keywords are found
            header_match_threshold = 3
            is_header_row = found_header_keywords >= header_match_threshold

            if is_header_row:
                header_list = EXPECTED_SPREADSHEETML_HEADERS
                header_row_index = i # Store the index of the header row
                logger.debug(f"Debug in xml_to_csv_spreadsheetml: Identified header row at index {header_row_index}.")
                break # Stop searching for header once found


        # If header was not found, we cannot proceed
        if not header_list or header_row_index is None:
            logger.debug("Debug in xml_to_csv_spreadsheetml: Header row not found.")
            return "" # Return empty CSV if header not found

        # --- Phase 2: Extract data rows after the header ---
        # Start processing rows immediately after the identified header row
        first_data_row_actual_index = header_row_index + 1
        logger.debug(f"Debug in xml_to_csv_spreadsheetml: Starting data row extraction from index {first_data_row_actual_index}...")

        for i in range(first_data_row_actual_index, len(rows)):
            row = rows[i]
            row_values = []
            current_cell_index = 1

            # Extract cell values for the current data row
            for cell in row.findall('.//ss:Cell', namespaces):
                index_attr = cell.get(f'{{{SS_NAMESPACE}}}Index')
                if index_attr:
                    cell_index = int(index_attr)
                    while current_cell_index < cell_index:
                        row_values.append("")
                        current_cell_index += 1
                    current_cell_index = cell_index

                data_element = cell.find('.//ss:Data', namespaces)
                cell_value = ""
                if data_element is not None:
                    cell_value = ''.join(data_element.itertext()).strip() # Strip whitespace

                row_values.append(cell_value)
                current_cell_index += 1

            # Check if the row is not empty and the first column looks like a date
            # This helps filter out summary rows or other non-data rows that might appear after the header
            is_potential_data_row = row_values and len(row_values) > 0 and row_values[0] and isinstance(row_values[0], str) and (re.match(r'\d{4}-\d{2}-\d{2}T', row_values[0]) or re.match(r'\d{2}/\d{2}/\d{4}', row_values[0])) # Basic date pattern check

            if is_potential_data_row:
                # Add the data row values
                # Ensure the row has enough columns to match the header, pad with None if not
                padded_row = row_values + [None] * (len(header_list) - len(row_values))
                data_rows.append(padded_row)
                # logger.debug(f"Debug in xml_to_csv_spreadsheetml: Added row {i} to data_rows.") # Keep minimized
            # else:
                # logger.debug(f"Debug in xml_to_csv_spreadsheetml: Skipping potential non-data row at index {i}.") # Keep minimized


        # --- Write headers and data rows to CSV ---
        if header_list and data_rows:
            csv_writer.writerow(header_list) # Write the extracted headers
            csv_writer.writerows(data_rows) # Write the extracted data rows
            csv_string = csv_output.getvalue()
            logger.debug(f"Debug in xml_to_csv_spreadsheetml: Successfully extracted {len(data_rows)} data rows from SpreadsheetML. Converted to CSV string.")
            return csv_string
        else:
            logger.debug("Debug in xml_to_csv_spreadsheetml: No data rows found after header in SpreadsheetML.")
            return "" # Return empty CSV if no data rows found after header

    except ET.ParseError as e:
        logger.error(f"Debug in xml_to_csv_spreadsheetml: Error parsing XML as SpreadsheetML: {e}", exc_info=True)
        return ""
    except Exception as e:
        logger.error(f"Debug in xml_to_csv_spreadsheetml: An unexpected error occurred during SpreadsheetML parsing: {e}", exc_info=True)
        return ""


# Add a new function to parse the generic XML format
def generic_xml_to_list_of_dicts(xml_content: bytes):
    """
    Converts a generic XML format (like the one generated by the user's converter)
    to a list of dictionaries.
    Looks for <record> elements and extracts data from nested tags.
    Attempts to convert 'Amount' column to float and date strings to datetime objects.
    Includes debug logging.

    Args:
        xml_content: The raw byte content of the generic XML file.

    Returns:
        A tuple containing:
        - header_list (list): List of column headers (tag names found in records).
        - list_of_dicts (list): List of dictionaries, each representing a record.
        - error_message (str or None): An error message if conversion failed.
    """
    header_list = []
    list_of_dicts = []
    error_message = None

    try:
        root = ET.fromstring(xml_content)
        logger.debug("Debug in generic_xml_to_list_of_dicts: Successfully parsed XML.")

        records = root.findall('.//record') # Find all <record> elements
        logger.debug(f"Debug in generic_xml_to_list_of_dicts: Found {len(records)} <record> elements.")

        if not records:
            error_message = "No <record> elements found in the XML."
            logger.debug(f"Debug in generic_xml_to_list_of_dicts: {error_message}")
            return [], [], error_message

        # Determine headers from the tags in the first record (assuming consistent structure)
        if records[0] is not None:
            header_list = [elem.tag for elem in records[0] if elem.tag is not ET.Comment and elem.tag is not ET.ProcessingInstruction]
            logger.debug(f"Debug in generic_xml_to_list_of_dicts: Identified {len(header_list)} headers from first record.")
        else:
            logger.debug("Debug in generic_xml_to_list_of_dicts: First record element is None.")


        # Process each record
        for record in records:
            row_dict = {}
            # Extract data from each expected header tag within the record
            for header in header_list:
                element = record.find(header) # Find the element with the tag name matching the header
                cell_value = None
                if element is not None:
                    cell_value = ''.join(element.itertext()).strip() # Extract text and strip whitespace

                # --- Data Type Conversion Logic for Generic XML ---
                if isinstance(header, str):
                    if header.lower() == 'amount':
                        try:
                            # Use the helper function for amount parsing
                            amount_value = clean_and_parse_amount(cell_value)
                            row_dict[header] = amount_value

                        except (ValueError, TypeError) as e:
                            logger.debug(f"Debug in generic_xml_to_list_of_dicts: Could not convert Amount value '{cell_value}' to float for column '{header}': {e}")
                            row_dict[header] = None # Set to None if conversion fails

                    elif header.lower() == 'date':
                         # Use the helper function for date parsing
                         cleaned_date = clean_and_format_date(cell_value)
                         row_dict[header] = cleaned_date


                    else:
                        # For other headers, just store the extracted string value
                        row_dict[header] = cell_value

                else:
                    # If header is not a string (unexpected), just store the value
                    row_dict[header] = cell_value


            if row_dict and any(row_dict.values()):
                list_of_dicts.append(row_dict)

        if not list_of_dicts:
             error_message = error_message if error_message else "No data rows extracted from <record> elements."
             logger.debug(f"Debug in generic_xml_to_list_of_dicts: {error_message}")
        elif not header_list:
             error_message = error_message if error_message else "No header tags found in <record> elements."
             logger.debug(f"Debug in generic_xml_to_list_of_dicts: {error_message}")


    except ET.ParseError as e:
        error_message = f"Error parsing generic XML: {e}"
        logger.error(f"Debug in generic_xml_to_list_of_dicts: {error_message}", exc_info=True)
        header_list = []
        list_of_dicts = []
    except Exception as e:
        error_message = f"An unexpected error occurred during generic XML parsing: {e}"
        logger.error(f"Debug in generic_xml_to_list_of_dicts: {error_message}", exc_info=True)
        header_list = []
        list_of_dicts = []


    return header_list, list_of_dicts, error_message