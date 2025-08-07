import logging
from typing import List
from config import CHROMA_COLLECTION_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def index_documents(chroma_client, embedding_function, documents: List[str], metadatas: List[dict], ids: List[str], filename: str):
    """
    Mengindeks potongan teks yang telah diperkaya ke dalam vector store ChromaDB.

    Fungsi ini menggunakan `get_or_create_collection` untuk memastikan semua data dari
    seluruh dokumen disimpan dalam satu koleksi yang konsisten. Penggunaan `cosine`
    sebagai metrik jarak adalah praktik standar untuk model embedding berbasis transformer,
    karena efektif mengukur kesamaan semantik.

    Args:
        chroma_client: Instance client ChromaDB yang aktif.
        embedding_function: Fungsi embedding yang akan digunakan oleh ChromaDB.
        documents (List[str]): Daftar potongan teks yang akan diindeks.
        metadatas (List[dict]): Daftar metadata yang sesuai untuk setiap potongan.
        ids (List[str]): Daftar ID unik untuk setiap potongan.
        filename (str): Nama file asli, untuk keperluan logging dan metadata.
    """
    if not documents:
        logger.warning(f"Tidak ditemukan potongan teks untuk diindeks dari file '{filename}'.")
        return

    logger.info(f"Memulai proses indexing untuk {len(documents)} potongan teks dari '{filename}' ke ChromaDB...")
    try:
        collection = chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        logger.info(f"Berhasil mengindeks {len(documents)} potongan teks dari '{filename}'.")
    except Exception as e:
        logger.error(f"Terjadi kegagalan saat proses indexing untuk '{filename}': {e}", exc_info=True)
        raise
