import logging
from config import REPHRASE_QUESTION_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _format_chat_history(chat_history: list[dict]) -> str:
    """
    Memformat riwayat percakapan dari struktur list-of-dict menjadi string tunggal.

    Tujuan dari pemformatan ini adalah untuk menyajikan riwayat percakapan dalam format
    yang sederhana dan mudah dibaca oleh LLM saat membuat pertanyaan mandiri.

    Args:
        chat_history (list[dict]): Riwayat percakapan dalam format standar aplikasi.

    Returns:
        str: String yang berisi seluruh dialog percakapan.
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
    Memformulasikan ulang pertanyaan pengguna menjadi pertanyaan mandiri (standalone).

    Dalam alur RAG percakapan, pencarian konteks (retrieval) tidak memiliki akses ke
    seluruh riwayat chat. Oleh karena itu, pertanyaan lanjutan seperti "bagaimana dengan dia?"
    harus diubah menjadi pertanyaan lengkap seperti "bagaimana status proyek Kimi Dandy?"
    agar proses retrieval bisa efektif.

    Args:
        query (str): Pertanyaan lanjutan dari pengguna.
        chat_history (list): Riwayat percakapan sebelumnya untuk memberikan konteks.
        chat_model: Instance model bahasa yang telah diinisialisasi.

    Returns:
        str: Pertanyaan yang telah diformulasikan ulang. Mengembalikan pertanyaan asli
             jika terjadi kesalahan atau jika tidak ada riwayat percakapan.
    """
    if not chat_history:
        logger.info("Tidak ada riwayat percakapan, mengembalikan kueri asli.")
        return query

    formatted_history = _format_chat_history(chat_history)
    prompt = REPHRASE_QUESTION_PROMPT.format(chat_history=formatted_history, query=query)

    try:
        logger.info("Memulai formulasi ulang pertanyaan dengan konteks riwayat...")
        response = await chat_model.ainvoke(prompt)
        
        standalone_question = response.content.strip()
        
        if standalone_question.lower() != query.lower():
            logger.info(f"Kueri asli: '{query}'")
            logger.info(f"Kueri setelah formulasi ulang: '{standalone_question}'")
        
        return standalone_question
    except Exception as e:
        logger.error(f"Terjadi kesalahan saat formulasi ulang pertanyaan: {e}", exc_info=True)
        return query
