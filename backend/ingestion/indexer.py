import chromadb
import logging
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter
from core.config import EMBEDDING_MODEL_NAME, CHROMA_PATH, CHROMA_COLLECTION_NAME

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_and_store_embeddings(extracted_text: str):
    """
    Processes extracted text by chunking, embedding, and storing it in ChromaDB.

    Args:
        extracted_text: The text content extracted from a document.
    """
    logger.info("Starting the process of chunking, embedding, and indexing.")

    # 1. Initialize Text Splitter
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    # 2. Perform Chunking
    chunks = text_splitter.split_text(extracted_text)
    logger.info(f"Text split into {len(chunks)} chunks.")

    # 3. Initialize ChromaDB Client
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    logger.info(f"Connected to ChromaDB at {CHROMA_PATH}.")

    # 4. Initialize Embedding Function
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )
    logger.info(f"Initialized Sentence Transformer with model: {EMBEDDING_MODEL_NAME}.")

    # 5. Get or Create Collection
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=sentence_transformer_ef,
    )
    logger.info(f"Accessed or created collection: {CHROMA_COLLECTION_NAME}.")

    # 6. Create Unique IDs
    ids = [f"chunk_{i}" for i, _ in enumerate(chunks)]
    logger.info(f"Generated {len(ids)} unique IDs for the chunks.")

    # 7. Add to Database
    collection.add(documents=chunks, ids=ids)
    logger.info(f"Successfully added {len(chunks)} document chunks to the collection.")
