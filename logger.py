"""Logging configuration for the video player application."""
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
    logger = logging.getLogger("videoplayer")
    
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


def get_logger(name: str = "videoplayer") -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__ or module name)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
