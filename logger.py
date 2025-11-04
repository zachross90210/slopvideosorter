"""
Slop Video Sorter: Logging configuration for the video player application.

Copyright (C) 2025 zachross90210 <zachross90210@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import logging
import sys
from pathlib import Path


def setup_logger(verbosity: int = 0) -> logging.Logger:
    """
    Set up the application logger with appropriate verbosity level.
    
    Args:
        verbosity: Verbosity level (0=ERROR, 1=WARNING, 2=INFO, 3=DEBUG)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("slopvideosorter")
    
    # Don't add handlers if they already exist (avoid duplicates)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)  # Logger captures all levels
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stderr)
    
    # Set handler level based on verbosity
    if verbosity >= 3:
        console_handler.setLevel(logging.DEBUG)
    elif verbosity == 2:
        console_handler.setLevel(logging.INFO)
    elif verbosity == 1:
        console_handler.setLevel(logging.WARNING)
    else:
        console_handler.setLevel(logging.ERROR)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = "slopvideosorter") -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__ or module name)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
