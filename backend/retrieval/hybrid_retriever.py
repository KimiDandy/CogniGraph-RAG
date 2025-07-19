import logging
import google.generativeai as genai
from .qa_chain import vector_search_tool
from core.config import LLM_MODEL_NAME, GOOGLE_API_KEY
from typing import List, Dict, Optional

# Configure logging and AI model
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
genai.configure(api_key=GOOGLE_API_KEY)

async def get_answer(query: str, filenames: List[str], chat_history: Optional[List[Dict[str, str]]]) -> str:
    """
    Retrieves an answer from the new Context-Enriched RAG architecture.
    It performs a single, powerful vector search against 'super-chunks' and generates a final answer.
    """
    logger.info(f"Initiating enriched RAG for query: '{query}' on files: {filenames}")

    # 1. Rephrase Question (if history exists)
    # ========================================
    rephrased_query = query
    if chat_history and len(chat_history) > 1: # more than just the initial assistant message
        logger.info("Chat history detected. Rephrasing question...")
        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
        rephrase_prompt = f"""
        Berdasarkan riwayat percakapan berikut dan pertanyaan terakhir, buatlah pertanyaan mandiri yang dapat dipahami tanpa konteks riwayat.

        Riwayat Percakapan:
        {history_str}

        Pertanyaan Terakhir: {query}

        Pertanyaan Mandiri:
        """
        try:
            model = genai.GenerativeModel(LLM_MODEL_NAME)
            response = await model.generate_content_async(rephrase_prompt)
            rephrased_query = response.text.strip()
            logger.info(f"Rephrased query: '{rephrased_query}'")
        except Exception as e:
            logger.error(f"Error during question rephrasing: {e}", exc_info=True)
            # Proceed with original query if rephrasing fails
            rephrased_query = query

    # 2. Retrieve Enriched Context
    # ==============================
    context = await vector_search_tool(rephrased_query, filenames)
    if not context:
        logger.warning("Vector search returned no context. Cannot generate answer.")
        return "Maaf, saya tidak menemukan informasi yang relevan dengan pertanyaan Anda di dalam dokumen."

    logger.info(f"Retrieved enriched context. Length: {len(context)}")

    # 3. Final Answer Generation
    # ==========================
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
