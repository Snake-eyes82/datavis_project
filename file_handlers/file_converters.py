# In file_handlers/file_converters.py - Copy and paste this ENTIRE code block into the file

import pandas as pd # Import the pandas library
import xml.etree.ElementTree as ET # For XML parsing
import json, datetime, os, re, io, csv, xml # For working with JSON data
import pyexcel

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

