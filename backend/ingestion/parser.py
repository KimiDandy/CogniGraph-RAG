from unstructured.partition.auto import partition
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def parse_document(file_path: str) -> str:
    """
    Asynchronously parses a document from a given file path and extracts its text content.

    Args:
        file_path: The path to the document file.

    Returns:
        A string containing the extracted text, or an error message if parsing fails.
    """
    logger.info(f"Starting parsing for document: {file_path}")
    try:
        # Use unstructured's partition function to parse the document based on its type
        elements = partition(filename=file_path)
        
        # Join the text from all extracted elements with a double newline for separation
        extracted_text = "\n\n".join([el.text for el in elements])
        
        logger.info(f"Successfully parsed document: {file_path}")
        return extracted_text
    except FileNotFoundError:
        logger.error(f"File not found at path: {file_path}")
        return f"Error: File not found at {file_path}"
    except Exception as e:
        # Catch other potential errors from the parsing library
        logger.error(f"An error occurred during parsing of {file_path}: {e}", exc_info=True)
        return f"Error: An unexpected error occurred during parsing: {str(e)}"
