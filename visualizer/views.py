# In visualizer/views.py

# 0.0 Required Imports
# --------------------
# 0.1 Standard library imports
import os
import io # Used for StringIO
import xml.etree.ElementTree as ET # Used for XML logic fallback (though ideally in converter)
import json # Used for JSON handling
import re # Used in the view for file extension check
from datetime import datetime # Used for type checking if needed (though converters handle most)
import logging # Python's built-in logging module

# 0.2 Django imports
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse # Added JsonResponse import
from django.conf import settings
from django.views.decorators.http import require_POST # Useful decorator for POST-only views

# 0.3 Third-party imports
import pandas as pd # Used for DataFrame in saving XLSX
import xlsxwriter # Used for saving XLSX
# pyexcel is not used directly in views.py anymore with refactored converters
from .forms import XMLUploadForm # Assuming you have a form for file upload

# Import the specific conversion functions from their new locations
# Note the path: file_handlers.converters.<module_name>
from file_handlers.converters.csv import csv_to_list_of_dicts
from file_handlers.converters.xlsx import xlsx_to_list_of_dicts
from file_handlers.converters.ods_handler import ods_to_list_of_dicts
from file_handlers.converters.xml import xml_to_csv_spreadsheetml, generic_xml_to_list_of_dicts
from file_handlers.converters.json import json_to_list_of_dicts

# Get a logger instance for this module
logger = logging.getLogger(__name__)


# 1.0 View for handling file upload and conversion
# ------------------------------------------------
# This view now handles the upload, determines file type, converts data to list of dicts,
# saves XLSX, stores processed data in session, and redirects to the data table.
# @require_POST # Optional: Decorator to ensure only POST requests are allowed
def upload_file_view(request):
    # Initialize form for GET requests
    if request.method == 'GET':
        form = XMLUploadForm()
        # Clear previous session data on GET request to upload page
        request.session.pop('raw_uploaded_content', None)
        request.session.pop('uploaded_filename', None)
        request.session.pop('extracted_header', None)
        request.session.pop('extracted_data_rows_list_of_dicts', None)
        request.session.pop('conversion_error', None)
        logger.debug("Debug in upload_file_view: GET request - Rendering upload form.")
        return render(request, 'visualizer/upload_form.html', {'form': form})

    # Handle POST request for file upload
    elif request.method == 'POST':
        form = XMLUploadForm(request.POST, request.FILES)

        # Clear previous session data before processing new upload
        # (Moved from outside the if/else block to be specific to POST processing start)
        request.session.pop('raw_uploaded_content', None)
        request.session.pop('uploaded_filename', None)
        request.session.pop('extracted_header', None)
        request.session.pop('extracted_data_rows_list_of_dicts', None)
        request.session.pop('conversion_error', None)


        if form.is_valid():
            uploaded_file = form.cleaned_data['xml_file']

            header_list = []
            list_of_dicts = []
            error_message = None
            file_type = None
            uploaded_filename = uploaded_file.name

            logger.debug(f"Debug in upload_file_view: Processing file: {uploaded_filename}")

            # --- Determine file type and call appropriate converter ---
            if uploaded_filename:
                base_name, extension_with_dot = os.path.splitext(uploaded_filename)
                file_extension = str(extension_with_dot).lower()

                logger.debug(f"Debug in upload_file_view: File extension: {file_extension}")

                try:
                    raw_file_content = uploaded_file.read()
                    logger.debug(f"Debug in upload_file_view: Raw file content type: {type(raw_file_content)}")

                    # --- Handle XLSX files ---
                    if file_extension in ['.xlsx', '.xls']:
                        file_type = 'xlsx'
                        logger.debug("Debug in upload_file_view: Handling XLSX.")
                        header_list, list_of_dicts, error_message = xlsx_to_list_of_dicts(raw_file_content)

                    # --- Handle CSV files ---
                    elif file_extension == '.csv':
                        file_type = 'csv'
                        logger.debug("Debug in upload_file_view: Handling CSV.")
                        try:
                            csv_content_string = raw_file_content.decode('utf-8')
                            csv_file_like_object = io.StringIO(csv_content_string)
                            header_list, list_of_dicts, error_message = csv_to_list_of_dicts(csv_file_like_object)
                        except Exception as e:
                            error_message = f"Error decoding or processing CSV: {e}"
                            logger.error(f"Debug in upload_file_view: {error_message}", exc_info=True)


                    # --- Handle ODS files ---
                    elif file_extension == '.ods':
                        file_type = 'ods'
                        logger.debug("Debug in upload_file_view: Handling ODS.")
                        header_list, list_of_dicts, error_message = ods_to_list_of_dicts(raw_file_content)


                    # --- Handle JSON files ---
                    elif file_extension == '.json':
                        file_type = 'json'
                        logger.debug("Debug in upload_file_view: Handling JSON.")
                        # Call the json_to_list_of_dicts function
                        header_list, list_of_dicts, error_message = json_to_list_of_dicts(raw_file_content)


                    # --- Handle XML files (try generic first, then SpreadsheetML) ---
                    elif file_extension == '.xml':
                        file_type = 'xml'
                        logger.debug("Debug in upload_file_view: Handling XML.")
                        try:
                            # Attempt to parse as generic XML first
                            logger.debug("Debug in upload_file_view: Attempting to parse as generic XML.")
                            header_list, list_of_dicts, error_message = generic_xml_to_list_of_dicts(raw_file_content)

                            if not list_of_dicts: # If generic parsing didn't yield data
                                logger.debug("Debug in upload_file_view: Generic XML parsing failed or found no data. Attempting SpreadsheetML XML.")
                                # Fallback to SpreadsheetML parsing
                                # Note the updated function name
                                csv_string_from_xml = xml_to_csv_spreadsheetml(raw_file_content)

                                if csv_string_from_xml:
                                    logger.debug("Debug in upload_file_view: SpreadsheetML XML converted to CSV. Processing CSV...")
                                    csv_file_like_object = io.StringIO(csv_string_from_xml)
                                    header_list, list_of_dicts, error_message = csv_to_list_of_dicts(csv_file_like_object)
                                else:
                                    # If both XML parsing attempts failed
                                    error_message = error_message if error_message else "XML conversion failed (neither generic nor SpreadsheetML format recognized or contained data)."
                                    logger.debug(f"Debug in upload_file_view: {error_message}")
                            else:
                                logger.debug("Debug in upload_file_view: Successfully parsed as generic XML.")


                        except Exception as e:
                            error_message = f"An error occurred during XML processing: {e}"
                            logger.error(f"Debug in upload_file_view: {error_message}", exc_info=True)


                    else:
                        file_type = 'unsupported'
                        error_message = f"Unsupported file type: {file_extension}"
                        logger.debug(f"Debug in upload_file_view: {error_message}")


                except Exception as e:
                    logger.error(f"Error reading uploaded file: {e}", exc_info=True)
                    error_message = f"Error processing file: {e}"


            else:
                file_type = 'unknown'
                error_message = "Could not determine file type."
                logger.debug(f"Debug in upload_file_view: {error_message}")


            # --- Store the standardized data and any error in the user's session ---
            # Ensure datetime objects are converted to strings for JSON serialization
            if list_of_dicts:
                logger.debug(f"Debug in upload_file_view: Preparing {len(list_of_dicts)} rows for session storage.")
                for row_dict in list_of_dicts:
                    for key, value in row_dict.items():
                        # Check if the value is a datetime object before calling isoformat()
                        # datetime can be from the standard library or pandas.Timestamp, check for both
                        if isinstance(value, (datetime, pd.Timestamp)):
                            try:
                                # Convert to ISO 8601 format string
                                row_dict[key] = value.isoformat()
                                # logger.debug(f"Debug in upload_file_view: Converted datetime object for key '{key}' to string for session.") # Minimize print
                            except Exception as e:
                                logger.debug(f"Debug in upload_file_view: Error converting datetime object for key '{key}' to string: {e}")
                                row_dict[key] = str(value) # Fallback to string conversion

            request.session['extracted_header'] = header_list
            request.session['extracted_data_rows_list_of_dicts'] = list_of_dicts
            if error_message:
                request.session['conversion_error'] = error_message
                logger.debug(f"Debug in upload_file_view: Conversion error stored in session: {error_message}")
            else:
                logger.debug(f"Debug in upload_file_view: Successfully converted {len(list_of_dicts) if list_of_dicts else 0} rows and {len(header_list) if header_list else 0} headers. Stored in session.")


            # --- Save the converted data as an XLSX file (optional) ---
            # Save only if conversion was successful and produced data
            if list_of_dicts and not error_message:
                try:
                    filename_base = os.path.splitext(uploaded_filename)[0].replace(' ', '_')
                    saved_filename = f"{filename_base}_converted.xlsx"
                    # Define the full path to save the file
                    # Ensure MEDIA_ROOT is configured in settings.py
                    save_path = os.path.join(settings.MEDIA_ROOT, saved_filename)

                    # Create MEDIA_ROOT directory if it doesn't exist
                    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

                    # Convert the list of dictionaries to a pandas DataFrame
                    # Provide headers explicitly to ensure correct column order/names if data_rows is empty
                    df_to_save = pd.DataFrame(list_of_dicts, columns=header_list if header_list else None)

                    # Use BytesIO to write the Excel file in memory
                    output = io.BytesIO()
                    # Specify the engine explicitly
                    writer = pd.ExcelWriter(output, engine='openpyxl')
                    df_to_save.to_excel(writer, index=False, sheet_name='Sheet1')
                    writer.close() # Use close() instead of save() with newer pandas/openpyxl
                    xlsx_data = output.getvalue()

                    # Write the bytes content to the file
                    with open(save_path, 'wb') as f:
                        f.write(xlsx_data)

                    logger.debug(f"Debug in upload_file_view: XLSX file saved to: {save_path}")

                except Exception as e:
                    logger.error(f"Error saving XLSX file: {e}", exc_info=True)
                    # Store saving error if no conversion error already exists
                    if not request.session.get('conversion_error'):
                        request.session['conversion_error'] = f"Error saving converted file: {e}"
                        logger.debug("Debug in upload_file_view: XLSX saving error stored.")


            # --- Redirect directly to the data table page ---
            # Redirect regardless of saving XLSX, but only if the form was valid
            logger.debug("Debug in upload_file_view: Redirecting to data table page.")
            return redirect('visualizer:visualizer_interface')


        else: # Form is not valid
            logger.debug("Debug in upload_file_view: Form is not valid.")
            # Set a conversion error message for invalid form
            request.session['conversion_error'] = "Please select a file to upload."
            # Render the upload form again with the form and error message
            return render(request, 'visualizer/upload_form.html', {'form': form, 'conversion_error': request.session.get('conversion_error')})


    # Add handling for other request methods if necessary (e.g., HEAD, OPTIONS)
    else:
        logger.warning(f"Debug in upload_file_view: Received unsupported HTTP method: {request.method}")
        return HttpResponse("Method Not Allowed", status=405)


# 3.0 View for displaying the extracted data table
# ------------------------------------------------
def visualizer_interface(request):
    extracted_data_list = request.session.get('extracted_data_rows_list_of_dicts', [])
    extracted_header = request.session.get('extracted_header', [])
    conversion_error = request.session.get('conversion_error', None)

    logger.debug(f"Debug in visualizer_interface: Retrieved {len(extracted_header)} headers from session.")
    logger.debug(f"Debug in visualizer_interface: Retrieved {len(extracted_data_list)} data rows from session.")
    if conversion_error:
        logger.debug(f"Debug in visualizer_interface: Conversion error: {conversion_error}")


    context = {
        'extracted_header': extracted_header,
        'extracted_data_rows_list_of_dicts': extracted_data_list,
        'conversion_error': conversion_error,
    }

    logger.debug("Debug in visualizer_interface: Rendering visualizer_interface.html")
    return render(request, 'visualizer/visualizer_interface.html', context)

# 4.0 View for displaying the chart only
# -------------------------------------
def chart_only_view(request):
    extracted_data_list = request.session.get('extracted_data_rows_list_of_dicts', [])
    extracted_header = request.session.get('extracted_header', [])
    conversion_error = request.session.get('conversion_error', None)

    logger.debug(f"Debug in chart_only_view: Retrieved {len(extracted_header)} headers from session.")
    logger.debug(f"Debug in chart_only_view: Retrieved {len(extracted_data_list)} data rows from session.")
    if conversion_error:
        logger.debug(f"Debug in chart_only_view: Conversion error: {conversion_error}")


    # Prepare data for the chart (assuming JSON format is needed by your JS)
    extracted_data_json_string = "[]" # Default to empty JSON array
    try:
        # Convert the list of dictionaries to a JSON string for the JavaScript
        # Use default=str to handle any remaining non-serializable objects (like datetime if not converted earlier)
        # Ensure only valid JSON data is included
        json_serializable_data = []
        if extracted_data_list:
             # Simple deep conversion to string for all values to ensure JSON serializability
             # More robust handling might be needed depending on data types
             json_serializable_data = [{key: str(value) if value is not None else None for key, value in row.items()} for row in extracted_data_list]


        extracted_data_json_string = json.dumps(json_serializable_data, separators=(',', ':'))
        logger.debug("Debug in chart_only_view: Successfully serialized data to JSON string.")

    except Exception as e:
        logger.error(f"Error serializing data to JSON for chart: {e}", exc_info=True)
        # If serialization fails here, it's a fallback error, the main conversion should handle types
        extracted_data_json_string = "[]" # Ensure it's still valid JSON


    context = {
        'extracted_header': extracted_header,
        'extracted_data_json_string': extracted_data_json_string,
        'conversion_error': conversion_error,
        'extracted_data_rows_list_of_dicts': extracted_data_list, # Keep for the template check
    }

    logger.debug("Debug in chart_only_view: Rendering chart_only.html")
    return render(request, 'visualizer/chart_only.html', context)
