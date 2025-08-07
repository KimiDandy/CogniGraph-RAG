import logging
from typing import List, Dict, Optional
from .qa_chain import vector_search_tool
from .conversational_logic import rephrase_question_with_history
from config import FINAL_ANSWER_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_answer(query: str, filenames: List[str], chat_history: Optional[List[Dict[str, str]]], chat_model, chroma_client, embedding_function) -> str:
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

    rephrased_query = await rephrase_question_with_history(query, chat_history, chat_model)

    context = await vector_search_tool(rephrased_query, filenames, chroma_client, embedding_function)
    if not context:
        logger.warning("Vector search returned no context. Cannot generate answer.")
        return "Maaf, saya tidak menemukan informasi yang relevan dengan pertanyaan Anda di dalam dokumen."

    logger.info(f"Retrieved enriched context. Length: {len(context)}")


    logger.info("Generating final answer from enriched context...")
    final_prompt = FINAL_ANSWER_PROMPT.format(context=context, rephrased_query=rephrased_query)

    try:
        final_response = await chat_model.ainvoke(final_prompt)
        logger.info("Final answer generated successfully.")
        return final_response.content
    except Exception as e:
        logger.error(f"Error during final answer generation: {e}", exc_info=True)
        return "Terjadi kesalahan saat menghasilkan jawaban akhir."
