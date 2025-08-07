import logging
from config import REPHRASE_QUESTION_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _format_chat_history(chat_history: list[dict]) -> str:
    """
    Memformat riwayat percakapan dari list of dict menjadi sebuah string tunggal.

    Args:
        chat_history (list[dict]): Riwayat percakapan dalam format standar.

    Returns:
        str: String yang berisi seluruh riwayat percakapan.
    """
    if not chat_history:
        return ""
    
    formatted_history = []
    for message in chat_history:
        role = "Human" if message["role"] == "user" else "AI"
        formatted_history.append(f"{role}: {message['content']}")
    
    return "\n".join(formatted_history)

async def rephrase_question_with_history(query: str, chat_history: list, chat_model) -> str:
    """
    Memformulasikan ulang pertanyaan pengguna berdasarkan riwayat percakapan.

    Tujuannya adalah untuk mengubah pertanyaan lanjutan yang mungkin ambigu
    (misalnya, "siapa namanya?") menjadi pertanyaan yang mandiri dan lengkap
    (misalnya, "siapa nama manajer TEFA?").

    Args:
        query (str): Pertanyaan lanjutan dari pengguna.
        chat_history (list): Riwayat percakapan sebelumnya.

    Returns:
        str: Pertanyaan yang telah diformulasikan ulang. Mengembalikan
             pertanyaan asli jika terjadi kesalahan atau tidak ada riwayat.
    """
    if not chat_history:
        logger.info("No chat history, returning original query.")
        return query

    formatted_history = _format_chat_history(chat_history)
    
    prompt = REPHRASE_QUESTION_PROMPT.format(chat_history=formatted_history, query=query)

    try:
        logger.info("Rephrasing question with history...")
        response = await chat_model.generate_content_async(prompt)
        
        standalone_question = response.text.strip()
        logger.info(f"Original query: '{query}'")
        logger.info(f"Rephrased question: '{standalone_question}'")
        
        return standalone_question
    except Exception as e:
        logger.error(f"Error during question rephrasing: {e}")

        return query
