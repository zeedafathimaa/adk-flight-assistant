# flight_search_assistant/flight_search_agent/utils/validate_date_format.py
import re
from datetime import datetime

def validate_date_format(date_str: str) -> bool:
    """Validate if a date string is in YYYY-MM-DD format.

    Args:
        date_str (str): Date string to validate

    Returns:
        bool: True if date is in valid YYYY-MM-DD format, False otherwise
    """
    # Check if the string matches the YYYY-MM-DD pattern
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_str):
        return False

    # Try parsing the date to ensure it's a real date (e.g., not 2023-02-30)
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        # The date string matched the pattern but is not a valid date
        return False