import chromadb
import logging
from chromadb.utils import embedding_functions
from core.config import EMBEDDING_MODEL_NAME, CHROMA_PATH, CHROMA_COLLECTION_NAME
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inisialisasi klien ChromaDB di tingkat modul untuk efisiensi
client = chromadb.PersistentClient(path=CHROMA_PATH)
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL_NAME)
collection = client.get_or_create_collection(
    name=CHROMA_COLLECTION_NAME,
    embedding_function=sentence_transformer_ef,
    metadata={"hnsw:space": "cosine"}
)

async def index_documents(documents: List[str], metadatas: List[dict], ids: List[str], filename: str):
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
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        logger.info(f"Successfully indexed {len(documents)} chunks for {filename}.")
    except Exception as e:
        logger.error(f"Failed during ChromaDB indexing for {filename}: {e}", exc_info=True)
        # Dilempar kembali untuk ditangani oleh pipeline
        raise
