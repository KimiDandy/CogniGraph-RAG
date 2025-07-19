import logging
import shutil
from pathlib import Path
from fastapi import UploadFile

from ingestion.parser import parse_document
from ingestion.indexer import process_and_store_embeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_DIRECTORY = Path("data/uploads")

async def process_document(file_path: str, filename: str, status_storage: dict):
    """
    The complete pipeline for ingesting a document, from saving to indexing.
    This function is designed to be run in the background.
    """
    try:
        logger.info(f"Starting document processing for: {file_path}")
        status_storage[filename] = {"status": "processing", "message": "Extracting text..."}

        # 1. Parse the document to extract text
        extracted_text = await parse_document(file_path=file_path)
        if extracted_text.startswith("Error:"):
            raise Exception(extracted_text)
        
        status_storage[filename] = {"status": "processing", "message": "Text extracted, indexing content..."}

        # 2. Index the document content (Graph + Vector)
        await process_and_store_embeddings(extracted_text, filename=filename)
        
        # 3. Mark as complete and include the extracted text
        logger.info(f"Successfully processed and indexed {filename}")
        status_storage[filename] = {
            "status": "complete", 
            "message": f"File '{filename}' processed successfully.",
            "text_content": extracted_text
        }

    except Exception as e:
        logger.error(f"Error processing {filename}: {e}", exc_info=True)
        status_storage[filename] = {"status": "error", "message": str(e)}
