import logging
import google.generativeai as genai
from .qa_chain import vector_search_tool
from .conversational_logic import rephrase_question_with_history
from core.config import LLM_MODEL_NAME, GOOGLE_API_KEY
from typing import List, Dict, Optional

# Configure logging and AI model
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
genai.configure(api_key=GOOGLE_API_KEY)

async def get_answer(query: str, filenames: List[str], chat_history: Optional[List[Dict[str, str]]]) -> str:
    """
    Mengorkestrasi alur RAG untuk menghasilkan jawaban berdasarkan kueri.

    Fungsi ini menjalankan tiga langkah utama:
    1.  **Rephrase:** Memformulasikan ulang pertanyaan pengguna jika ada riwayat
        percakapan untuk menjadikannya pertanyaan yang mandiri.
    2.  **Retrieve:** Mengambil konteks yang relevan dari dokumen yang dipilih
        menggunakan pencarian vektor pada 'super-chunks' yang diperkaya.
    3.  **Generate:** Menghasilkan jawaban akhir menggunakan LLM berdasarkan
        konteks yang telah diambil.

    Args:
        query (str): Pertanyaan dari pengguna.
        filenames (List[str]): Daftar file yang menjadi sumber jawaban.
        chat_history (Optional[List[Dict[str, str]]]): Riwayat percakapan.

    Returns:
        str: Jawaban akhir yang dihasilkan oleh model.
    """
    logger.info(f"Initiating enriched RAG for query: '{query}' on files: {filenames}")

    rephrased_query = await rephrase_question_with_history(query, chat_history)


    context = await vector_search_tool(rephrased_query, filenames)
    if not context:
        logger.warning("Vector search returned no context. Cannot generate answer.")
        return "Maaf, saya tidak menemukan informasi yang relevan dengan pertanyaan Anda di dalam dokumen."

    logger.info(f"Retrieved enriched context. Length: {len(context)}")


    logger.info("Generating final answer from enriched context...")
    model = genai.GenerativeModel(LLM_MODEL_NAME)

    final_prompt = f"""
    Anda adalah asisten AI yang cerdas dan ahli. Berdasarkan informasi yang sangat relevan di bawah ini—yang mencakup teks asli dan fakta-fakta kunci yang diekstrak—jawablah pertanyaan pengguna secara akurat dan langsung dalam Bahasa Indonesia.

    INFORMASI YANG DITEMUKAN (KONTEKS GABUNGAN):
    ---
    {context}
    ---

    PERTANYAAN PENGGUNA:
    {rephrased_query}

    JAWABAN ANDA:
    """

    try:
        final_response = await model.generate_content_async(final_prompt)
        logger.info("Final answer generated successfully.")
        return final_response.text
    except Exception as e:
        logger.error(f"Error during final answer generation: {e}", exc_info=True)
        return "Terjadi kesalahan saat menghasilkan jawaban akhir."
