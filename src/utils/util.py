from datetime import datetime, date
import re
import os


def convert_date_to_datetime(d: date) -> datetime:
    return datetime.combine(d, datetime.min.time())


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to contain only lowercase alphabetical characters.
    
    Rules:
    - Only lowercase alphabetical characters allowed
    - No special characters, numbers, or spaces
    - Preserve file extension if it exists
    - Use 'report' as default if filename becomes empty or invalid
    
    Args:
        filename: Original filename to sanitize
        
    Returns:
        Sanitized filename with only lowercase alphabetical characters
    """
    if not filename or not isinstance(filename, str):
        return "report"
    
    # Split filename and extension
    name, ext = os.path.splitext(filename.strip())
    
    if not name:
        return "report"
    
    # Remove all non-alphabetical characters and convert to lowercase
    sanitized_name = re.sub(r'[^a-zA-Z]', '', name).lower()
    
    # If sanitized name is empty, use default
    if not sanitized_name:
        sanitized_name = "report"
    
    # Reconstruct filename with extension (keep original extension)
    if ext:
        # Sanitize extension too - keep only alphabetical characters
        sanitized_ext = re.sub(r'[^a-zA-Z.]', '', ext).lower()
        if sanitized_ext and not sanitized_ext.startswith('.'):
            sanitized_ext = '.' + sanitized_ext
        return sanitized_name + (sanitized_ext if sanitized_ext != '.' else '')
    
    return sanitized_name
