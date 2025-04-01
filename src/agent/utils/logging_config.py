import logging
import sys

def setup_logging():
    """Configure logging for the application."""
    # Create a logger
    logger = logging.getLogger("ai-browser-agent")
    
    # Set the logging level to DEBUG to see all logs
    logger.setLevel(logging.DEBUG)
    
    # Create console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add formatter to handler
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger 