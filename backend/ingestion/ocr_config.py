import platform
import os
import logging
from unstructured_pytesseract import pytesseract
from core.config import TESSERACT_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def configure_tesseract():
    """
    Checks for the Tesseract executable and configures pytesseract.
    This is a robust way to ensure Tesseract is found, bypassing PATH issues.
    """
    if platform.system() == "Windows":
        logger.info("Windows OS detected. Checking for Tesseract...")
        if os.path.exists(TESSERACT_PATH):
            pytesseract.tesseract_cmd = TESSERACT_PATH
            logger.info(f"Tesseract path successfully configured to: {TESSERACT_PATH}")
        else:
            logger.error(f"Tesseract executable not found at the configured path: {TESSERACT_PATH}")
            logger.error("Please verify the TESSERACT_PATH in core/config.py or ensure Tesseract is in your system PATH.")
    else:
        # For Linux/macOS, we often rely on the PATH.
        logger.info(f"Non-Windows OS ({platform.system()}) detected. Assuming 'tesseract' is in PATH.")
