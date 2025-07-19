import logging
import google.generativeai as genai
from .qa_chain import vector_search_tool
from core.config import LLM_MODEL_NAME, GOOGLE_API_KEY

# Configure logging and AI model
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
genai.configure(api_key=GOOGLE_API_KEY)

async def get_answer(query: str, filename: str) -> str:
    """
    Retrieves an answer from the new Context-Enriched RAG architecture.
    It performs a single, powerful vector search against 'super-chunks' and generates a final answer.
    """
    logger.info(f"Initiating enriched RAG for query: '{query}' on file: '{filename}'")

    # 1. Retrieve Enriched Context
    # =============================
    context = await vector_search_tool(query, filename)
    if not context:
        logger.warning("Vector search returned no context. Cannot generate answer.")
        return "Maaf, saya tidak menemukan informasi yang relevan dengan pertanyaan Anda di dalam dokumen."

    logger.info(f"Retrieved enriched context. Length: {len(context)}")

    # 2. Final Answer Generation
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
    {query}

    JAWABAN ANDA:
    """

    try:
        final_response = await model.generate_content_async(final_prompt)
        logger.info("Final answer generated successfully.")
        return final_response.text
    except Exception as e:
        logger.error(f"Error during final answer generation: {e}", exc_info=True)
        return "Terjadi kesalahan saat menghasilkan jawaban akhir."
