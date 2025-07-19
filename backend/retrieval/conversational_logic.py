import google.generativeai as genai
import logging
from config import LLM_MODEL_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _format_chat_history(chat_history: list[dict]) -> str:
    """
    Formats the chat history into a single string.
    """
    if not chat_history:
        return ""
    
    formatted_history = []
    for message in chat_history:
        role = "Human" if message["role"] == "user" else "AI"
        formatted_history.append(f"{role}: {message['content']}")
    
    return "\n".join(formatted_history)

async def rephrase_question_with_history(query: str, chat_history: list) -> str:
    """
    Rephrases the user's question based on the chat history to make it a standalone question.
    """
    if not chat_history:
        logger.info("No chat history, returning original query.")
        return query

    formatted_history = _format_chat_history(chat_history)
    
    prompt = f"""Based on the following conversation history, rephrase the "Follow Up Input" to be a standalone question that contains all the necessary context from the chat history.

Chat History:
{formatted_history}

Follow Up Input: {query}

Standalone question:"""

    try:
        logger.info("Rephrasing question with history...")
        model = genai.GenerativeModel(LLM_MODEL_NAME)
        response = await model.generate_content_async(prompt)
        
        standalone_question = response.text.strip()
        logger.info(f"Original query: '{query}'")
        logger.info(f"Rephrased question: '{standalone_question}'")
        
        return standalone_question
    except Exception as e:
        logger.error(f"Error during question rephrasing: {e}")
        # Fallback to the original query in case of an error
        return query
