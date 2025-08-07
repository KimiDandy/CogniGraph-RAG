import logging
from typing import List
from config import CHROMA_COLLECTION_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def vector_search_tool(query: str, filenames: List[str], chroma_client, embedding_function) -> str:
    """
    Melakukan pencarian vektor di ChromaDB untuk mengambil potongan teks relevan.

    Fungsi ini berperan sebagai "tool" pencarian dalam alur RAG. Pencarian dibatasi
    secara spesifik pada dokumen yang dipilih pengguna (melalui `filenames`) untuk
    memastikan konteks jawaban tetap relevan dan tidak tercampur dengan informasi
    dari dokumen lain yang tidak terkait.

    Args:
        query (str): Pertanyaan atau kueri pencarian yang sudah diformulasi ulang.
        filenames (List[str]): Daftar nama file yang menjadi target pencarian.
        chroma_client: Instance client ChromaDB.
        embedding_function: Fungsi embedding yang digunakan.

    Returns:
        str: String gabungan dari potongan-potongan teks relevan (konteks).
             Mengembalikan string kosong jika tidak ada hasil atau terjadi error.
    """
    logger.info(f"Menjalankan pencarian vektor untuk kueri: '{query}'")
    logger.info(f"Pencarian dibatasi pada file: {filenames}")
    
    try:
        # Mengambil atau membuat koleksi di ChromaDB.
        chroma_collection = chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"} 
        )

        # Melakukan kueri dengan filter 'where' untuk membatasi pencarian
        # hanya pada dokumen yang metadatanya cocok dengan 'filenames'.
        results = chroma_collection.query(
            query_texts=[query], 
            n_results=5, # Mengambil 5 hasil teratas
            where={"source_document": {"$in": filenames}}
        )
        
        if not results or not results["documents"] or not results["documents"][0]:
            logger.warning("Pencarian vektor tidak menemukan dokumen yang cocok.")
            return ""
            
        # Menggabungkan semua potongan dokumen yang ditemukan menjadi satu konteks besar.
        vector_context = "\n\n".join(results["documents"][0])
        logger.info(f"Pencarian vektor selesai. Panjang konteks: {len(vector_context)} karakter.")
        return vector_context
    except Exception as e:
        logger.error(f"Terjadi kesalahan saat pencarian vektor: {e}", exc_info=True)
        return ""
