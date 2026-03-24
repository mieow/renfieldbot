import logging

log = logging.basicConfig(
    level=logging.INFO,  # Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Format for log messages
    datefmt='%Y-%m-%d %H:%M:%S'  # Optional: Custom format for timestamps
)

log = logging.getLogger("RENFIELD")
