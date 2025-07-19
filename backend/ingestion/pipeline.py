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
    """
    Orkestrasi lengkap untuk pemrosesan satu dokumen.

    Fungsi ini menjalankan seluruh pipeline ingestion:
    1. Mengekstrak teks dari dokumen (termasuk OCR jika diperlukan).
    2. Membuat dan menyimpan embedding untuk pencarian vektor.
    3. Membangun dan memperbarui knowledge graph.

    Args:
        file_path (str): Path absolut menuju file yang akan diproses.

    Raises:
        Exception: Meneruskan kembali exception yang terjadi selama proses
                   parsing atau indexing untuk ditangani oleh pemanggil.
    """
    filename = Path(file_path).name
    try:
        logger.info(f"Starting document processing for: {file_path}")
        
        text_content = await parse_document(file_path)
        if not text_content:
            raise ValueError("Gagal mengekstrak teks dari dokumen.")

        await process_and_store_embeddings(text_content, filename=filename)
        logger.info(f"Successfully processed and indexed {filename}")

    except Exception as e:
        logger.error(f"Error in processing pipeline for {filename}: {e}", exc_info=True)

        raise e
