"""
Common utilities for HTML5 to Video Converter.
"""
import os
import datetime
import re
from pathlib import Path


class ConversionLogger:
    """
    Logs conversion process with timestamps for debugging.
    
    Provides structured logging with millisecond precision timestamps
    for troubleshooting conversion issues.
    """
    
    def __init__(self):
        """Initialize logger with empty log and start time."""
        self.log_entries = []
        self.start_time = datetime.datetime.now()
    
    def log(self, message: str) -> str:
        """
        Add timestamped message to log.
        
        Args:
            message: Message to log
            
        Returns:
            Formatted log entry with timestamp
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}"
        self.log_entries.append(log_entry)
        return log_entry
    
    def get_log_text(self) -> str:
        """
        Get complete log as terminal-style text.
        
        Returns:
            All log entries joined by newlines
        """
        return "\n".join(self.log_entries)
    
    def get_elapsed_time(self) -> str:
        """
        Get elapsed time since logger creation.
        
        Returns:
            Elapsed time in seconds with 2 decimal places
        """
        elapsed = datetime.datetime.now() - self.start_time
        return f"{elapsed.total_seconds():.2f}s"


def rgb_to_hex(rgb_string: str) -> str:
    """
    Convert RGB color string to hex format.
    
    Args:
        rgb_string: RGB color (e.g., "rgb(255, 128, 0)")
        
    Returns:
        Hex color string (e.g., "#ff8000")
        
    Example:
        >>> rgb_to_hex("rgb(255, 128, 0)")
        "#ff8000"
    """
    if not rgb_string or not rgb_string.startswith('rgb'):
        return "#000000"
    
    rgb_match = re.search(r'(\d+),\s*(\d+),\s*(\d+)', rgb_string)
    if rgb_match:
        r, g, b = map(int, rgb_match.groups())
        return f"#{r:02x}{g:02x}{b:02x}"
    
    return "#000000"


def ensure_even_dimension(dimension: int) -> int:
    """
    Ensure dimension is even (required for H.264 encoding).
    
    H.264 codec requires even dimensions for yuv420p pixel format.
    This function rounds down odd dimensions to the nearest even number.
    
    Args:
        dimension: Width or height in pixels
        
    Returns:
        Even dimension (original if already even, or original-1 if odd)
        
    Example:
        >>> ensure_even_dimension(1920)
        1920
        >>> ensure_even_dimension(1919)
        1918
    """
    return dimension if dimension % 2 == 0 else dimension - 1


def find_html_file(extract_dir: str) -> Path:
    """
    Find the main HTML file in an extracted directory.
    
    Searches for HTML files and prioritizes index.html if found.
    
    Args:
        extract_dir: Directory containing extracted HTML5 content
        
    Returns:
        Path to main HTML file
        
    Raises:
        FileNotFoundError: If no HTML files are found
    """
    html_files = list(Path(extract_dir).rglob("*.html"))
    
    if not html_files:
        raise FileNotFoundError("No HTML files found in the archive")
    
    # Look for index.html first
    for html_file in html_files:
        if html_file.name.lower() in ['index.html', 'index.htm']:
            return html_file
    
    # Otherwise return first HTML file found
    return html_files[0]


def validate_zip_security(zip_ref) -> None:
    """
    Validate ZIP file for security issues.
    
    Checks for:
    - Empty ZIP files
    - ZIP bombs (too many files or too large uncompressed)
    - Path traversal attacks
    
    Args:
        zip_ref: Open ZipFile object
        
    Raises:
        ValueError: If security validation fails
    """
    from config import MAX_FILES_IN_ZIP, MAX_UNCOMPRESSED_SIZE
    
    files = zip_ref.namelist()
    
    # Check for empty ZIP
    if len(files) == 0:
        raise ValueError("ZIP file is empty")
    
    # Check for excessive file count (potential ZIP bomb)
    if len(files) > MAX_FILES_IN_ZIP:
        raise ValueError(
            f"ZIP contains too many files ({len(files)}). "
            f"Maximum {MAX_FILES_IN_ZIP} files allowed."
        )
    
    # Check total uncompressed size (prevent ZIP bombs)
    total_size = sum(info.file_size for info in zip_ref.infolist())
    if total_size > MAX_UNCOMPRESSED_SIZE:
        size_mb = total_size / (1024 * 1024)
        max_mb = MAX_UNCOMPRESSED_SIZE / (1024 * 1024)
        raise ValueError(
            f"Uncompressed size too large ({size_mb:.1f} MB). "
            f"Maximum {max_mb} MB allowed."
        )
    
    # Check for path traversal attacks
    for filename in files:
        # Normalize path and check for traversal attempts
        normalized = os.path.normpath(filename)
        if normalized.startswith('..') or os.path.isabs(normalized):
            raise ValueError(f"Unsafe file path in ZIP: {filename}")


def load_javascript_file(script_name: str) -> str:
    """
    Load JavaScript file from the same directory as this module.
    
    Args:
        script_name: Name of JavaScript file (e.g., "browser_scripts.js")
        
    Returns:
        JavaScript code as string
        
    Raises:
        FileNotFoundError: If JavaScript file doesn't exist
    """
    script_path = Path(__file__).parent / script_name
    with open(script_path, 'r', encoding='utf-8') as f:
        return f.read()


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "15.3 MB", "1.2 GB")
        
    Example:
        >>> format_file_size(1024)
        "1.0 KB"
        >>> format_file_size(1536000)
        "1.5 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_browser_binary_path() -> str:
    """
    Find available browser binary from predefined paths.
    
    Checks common installation locations for Chrome, Chromium, and Comet.
    
    Returns:
        Path to browser binary, or empty string if none found
    """
    from config import BROWSER_PATHS
    
    for path in BROWSER_PATHS:
        if os.path.exists(path):
            return path
    
    return ""

