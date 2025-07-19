import logging
import shutil
from pathlib import Path
from fastapi import UploadFile

from ingestion.parser import parse_document
from ingestion.indexer import process_and_store_embeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_DIRECTORY = Path("data/uploads")

async def process_document(file_path: str):
    filename = Path(file_path).name
    try:
        logger.info(f"Starting document processing for: {file_path}")
        
        # 1. Parse document
        text_content = await parse_document(file_path)
        if not text_content:
            raise ValueError("Failed to extract text from document.")

        # 2. Index content (Vector + Graph)
        await process_and_store_embeddings(text_content, filename=filename)
        logger.info(f"Successfully processed and indexed {filename}")

    except Exception as e:
        logger.error(f"Error in processing pipeline for {filename}: {e}", exc_info=True)
        # Re-raise the exception to be caught by the main endpoint
        raise e
