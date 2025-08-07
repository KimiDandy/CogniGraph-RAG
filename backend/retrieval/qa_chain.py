import logging
from typing import List
from config import CHROMA_COLLECTION_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def vector_search_tool(query: str, filenames: List[str], chroma_client, embedding_function) -> str:
    """
    Melakukan pencarian vektor di ChromaDB untuk mengambil potongan teks yang relevan.

    Fungsi ini berfungsi sebagai tool untuk mencari konteks dari data tidak terstruktur.
    Pencarian dibatasi hanya pada dokumen yang ditentukan oleh `filenames` untuk
    memastikan konteks berasal dari sumber yang benar.

    Args:
        query (str): Pertanyaan atau kueri pencarian dari pengguna.
        filenames (List[str]): Daftar nama file yang menjadi target pencarian.

    Returns:
        str: String berisi gabungan potongan teks relevan yang ditemukan.
             Mengembalikan string kosong jika tidak ada hasil atau terjadi error.
    """
    logger.info(f"Executing vector search for query: '{query}' on files: {filenames}")
    try:
        chroma_collection = chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        results = chroma_collection.query(
            query_texts=[query], 
            n_results=5, 
            where={"source_document": {"$in": filenames}}
        )
        
        if not results["documents"] or not results["documents"][0]:
            logger.info("Vector search returned no documents.")
            return ""
            
        vector_context = "\n\n".join(results["documents"][0])
        logger.info(f"Vector search completed. Context length: {len(vector_context)}")
        return vector_context
    except Exception as e:
        logger.error(f"Error during vector search: {e}", exc_info=True)
        return ""
