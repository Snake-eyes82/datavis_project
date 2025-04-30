# visualizer/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Custom template filter to allow accessing dictionary values by key
    in Django templates. Useful when keys contain spaces or special characters
    that cannot be accessed using dot notation.
    """
    # Check if the dictionary is valid and the key exists
    if isinstance(dictionary, dict):
        # Use .get() with a default of None to avoid KeyError if the key doesn't exist
        return dictionary.get(key, None)
    # If it's not a dictionary, return None or the input itself depending on desired behavior
    # Returning None is safer if the filter is expected to work on dicts
    return None

# You can add other custom filters here if needed
# @register.filter
# def another_filter(value):
#     # Filter logic here
#     return processed_value