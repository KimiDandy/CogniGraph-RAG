import logging
from typing import List
from config import CHROMA_COLLECTION_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def index_documents(chroma_client, embedding_function, documents: List[str], metadatas: List[dict], ids: List[str], filename: str):
    """
    Mengindeks dokumen (potongan teks) yang telah diproses ke dalam ChromaDB.
    
    Args:
        documents (List[str]): Daftar potongan teks yang akan diindeks.
        metadatas (List[dict]): Daftar metadata yang sesuai untuk setiap potongan.
        ids (List[str]): Daftar ID unik untuk setiap potongan.
        filename (str): Nama file asli, untuk keperluan logging.
    """
    if not documents:
        logger.warning(f"Tidak ada potongan teks untuk diindeks untuk file {filename}. Proses dibatalkan.")
        return

    logger.info(f"Mengindeks {len(documents)} potongan teks dari {filename} ke ChromaDB...")
    try:
        collection = chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"} # Standar industri
        )
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        logger.info(f"Successfully indexed {len(documents)} chunks for {filename}.")
    except Exception as e:
        logger.error(f"Failed during ChromaDB indexing for {filename}: {e}", exc_info=True)
        # Dilempar kembali untuk ditangani oleh pipeline
        raise
