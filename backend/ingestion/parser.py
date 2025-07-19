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
        # Use unstructured's partition function with the "hi_res" strategy
        # to automatically engage OCR for images within the document.
        elements = partition(filename=file_path, strategy="hi_res")
        
        # Join the text from all extracted elements with a double newline for separation
        extracted_text = "\n\n".join([el.text for el in elements])
        logger.info(f"Successfully parsed document. Total characters: {len(extracted_text)}")
        return extracted_text
    except Exception as e:
        logger.error(f"Failed to parse document {file_path}: {e}", exc_info=True)
        # Depending on requirements, you might want to return an empty string or re-raise
        return ""
