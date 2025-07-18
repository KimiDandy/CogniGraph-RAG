import chromadb
import logging
import google.generativeai as genai
from chromadb.utils import embedding_functions
from core.config import (
    GOOGLE_API_KEY,
    LLM_MODEL_NAME,
    EMBEDDING_MODEL_NAME,
    CHROMA_PATH,
    CHROMA_COLLECTION_NAME,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure the generative AI model
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("Google AI SDK configured successfully.")
except Exception as e:
    logger.error(f"Failed to configure Google AI SDK: {e}")

async def get_rag_answer(query: str, filename: str) -> str:
    """
    Retrieves a relevant context from ChromaDB and generates an answer using a LLM.

    Args:
        query: The user's question.

    Returns:
        The generated answer.
    """
    logger.info(f"Received query: {query}")

    # Initialize ChromaDB client and embedding function
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )
    collection = client.get_collection(
        name=CHROMA_COLLECTION_NAME, embedding_function=sentence_transformer_ef
    )

        # 1. Retrieve relevant documents from ChromaDB, filtering by the source document
    results = collection.query(
        query_texts=[query], 
        n_results=5, 
        where={"source_document": filename}
    )
    context = "\n".join(results["documents"][0])
    logger.info(f"Retrieved context: {context[:500]}...") # Log first 500 chars

    # 2. Create the prompt for the LLM
    prompt = f"""
    Anda adalah asisten AI yang ahli dalam menjawab pertanyaan berdasarkan konteks yang diberikan. Jawab pertanyaan berikut HANYA berdasarkan informasi dari konteks di bawah ini. Jika jawaban tidak ada dalam konteks, katakan "Maaf, saya tidak menemukan informasi mengenai hal tersebut di dalam dokumen."

    KONTEKS:
    {context}

    PERTANYAAN:
    {query}

    JAWABAN:
    """

    # 3. Call the LLM to generate the answer
    try:
        model = genai.GenerativeModel(LLM_MODEL_NAME)
        response = model.generate_content(prompt)
        logger.info("Successfully generated answer from LLM.")
        return response.text
    except Exception as e:
        logger.error(f"Error generating content from LLM: {e}")
        return "Error: Terjadi masalah saat berkomunikasi dengan model AI."
