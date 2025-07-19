import chromadb
import logging
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ingestion.graph_builder import extract_knowledge_graph_from_text, store_triplets_in_neo4j
from core.config import EMBEDDING_MODEL_NAME, CHROMA_PATH, CHROMA_COLLECTION_NAME

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_and_store_embeddings(extracted_text: str, filename: str):
    """
    Processes text by extracting a knowledge graph, enriching text chunks with graph facts,
    and then storing the enriched chunks as vector embeddings in ChromaDB.
    """
    if not extracted_text or not extracted_text.strip():
        logger.warning(f"Skipping embedding process for {filename} because no text was extracted.")
        return

    # 1. Knowledge Graph Extraction & Storage
    logger.info(f"Step 1: Extracting and storing knowledge graph for {filename}...")
    try:
        structured_data = await extract_knowledge_graph_from_text(extracted_text)
        if structured_data:
            await store_triplets_in_neo4j(structured_data)
        else:
            logger.info("No structured data extracted, proceeding with standard chunking.")
    except Exception as e:
        logger.error(f"Failed during knowledge graph processing for {filename}: {e}", exc_info=True)
        # Continue without graph enrichment if this step fails
        structured_data = None

    # 2. Text Chunking
    logger.info(f"Step 2: Chunking document text for {filename}...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_text(extracted_text)
    logger.info(f"Split text into {len(chunks)} chunks.")

    # 3. Context Enrichment
    logger.info(f"Step 3: Enriching {len(chunks)} chunks with graph context...")
    enriched_chunks = []
    if structured_data:
        for chunk in chunks:
            enrichment_text = ""
            for head, _, relation, tail, _ in structured_data:
                if str(head) in chunk or str(tail) in chunk:
                    enrichment_text += f"- Fact: {head} -> {relation.replace('_', ' ').title()} -> {tail}\n"
            
            if enrichment_text:
                enriched_chunks.append(f"{chunk}\n\n[Related Facts from Knowledge Graph]:\n{enrichment_text}")
            else:
                enriched_chunks.append(chunk)
    else:
        enriched_chunks = chunks # Use original chunks if no graph data

    logger.info(f"Finished enriching chunks. Total enriched chunks: {len(enriched_chunks)}")

    # 4. Indexing into ChromaDB
    if not enriched_chunks:
        logger.warning(f"No chunks to index for {filename}. Aborting.")
        return

    logger.info(f"Step 4: Indexing {len(enriched_chunks)} enriched chunks into ChromaDB...")
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL_NAME)
        collection = client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME, 
            embedding_function=sentence_transformer_ef,
            metadata={"hnsw:space": "cosine"}
        )

        ids = [f"{filename}_{i}" for i in range(len(enriched_chunks))]
        metadatas = [{"source_document": filename} for _ in enriched_chunks]

        collection.add(documents=enriched_chunks, metadatas=metadatas, ids=ids)
        logger.info(f"Successfully indexed {len(enriched_chunks)} enriched chunks for {filename}.")
    except Exception as e:
        logger.error(f"Failed during ChromaDB indexing for {filename}: {e}", exc_info=True)
        # Re-raise to be caught by the pipeline
        raise
