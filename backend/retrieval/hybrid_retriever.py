import logging
from typing import List, Dict, Optional
from .qa_chain import vector_search_tool
from .conversational_logic import rephrase_question_with_history
from config import FINAL_ANSWER_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_answer(query: str, filenames: List[str], chat_history: Optional[List[Dict[str, str]]], chat_model, chroma_client, embedding_function) -> str:
    """
    Mengorkestrasi alur RAG (Retrieval-Augmented Generation) untuk menghasilkan jawaban.

    Fungsi ini adalah inti dari logika tanya-jawab, yang menjalankan tiga langkah utama:
    1.  **Formulasi Ulang (Rephrase):** Jika ada riwayat percakapan, pertanyaan pengguna
        difokuskan ulang menjadi pertanyaan mandiri yang mengandung semua konteks relevan.
        Ini krusial untuk menangani pertanyaan lanjutan (e.g., "bagaimana dengan dia?").
    2.  **Pengambilan (Retrieve):** Mengambil konteks yang relevan dari dokumen yang dipilih
        menggunakan pencarian vektor. Konteks ini sudah diperkaya dengan informasi dari
        knowledge graph pada tahap ingesti.
    3.  **Pembangkitan (Generate):** Menghasilkan jawaban akhir menggunakan LLM berdasarkan
        pertanyaan yang telah diformulasi ulang dan konteks yang kaya.

    Args:
        query (str): Pertanyaan asli dari pengguna.
        filenames (List[str]): Daftar file yang relevan untuk pencarian konteks.
        chat_history (Optional[List[Dict[str, str]]]): Riwayat percakapan sebelumnya.
        chat_model: Instance model bahasa generatif.
        chroma_client: Instance client ChromaDB.
        embedding_function: Fungsi embedding yang digunakan.

    Returns:
        str: Jawaban akhir yang dihasilkan oleh model, atau pesan error jika gagal.
    """
    logger.info(f"Memulai alur RAG untuk kueri: '{query}' pada file: {filenames}")

    rephrased_query = await rephrase_question_with_history(query, chat_history, chat_model)
    if rephrased_query.lower() != query.lower():
        logger.info(f"Pertanyaan diformulasi ulang menjadi: '{rephrased_query}'")
    context = await vector_search_tool(rephrased_query, filenames, chroma_client, embedding_function)
    if not context:
        logger.warning(f"Pencarian vektor untuk '{rephrased_query}' tidak menemukan konteks.")
        return "Maaf, saya tidak dapat menemukan informasi yang relevan dengan pertanyaan Anda di dalam dokumen yang tersedia."

    logger.info(f"Berhasil mengambil konteks yang diperkaya. Panjang: {len(context)} karakter.")

    logger.info("Menghasilkan jawaban akhir dari konteks yang diperkaya...")
    final_prompt = FINAL_ANSWER_PROMPT.format(context=context, rephrased_query=rephrased_query)

    try:
        final_response = await chat_model.ainvoke(final_prompt)
        logger.info("Jawaban akhir berhasil dibuat.")
        return final_response.content
    except Exception as e:
        logger.error(f"Terjadi kesalahan saat pembuatan jawaban akhir: {e}", exc_info=True)
        return "Mohon maaf, terjadi kesalahan internal saat saya mencoba merumuskan jawaban."
