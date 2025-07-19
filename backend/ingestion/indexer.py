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
    # --- Guard Clause for Empty Text ---
    if not extracted_text or not extracted_text.strip():
        logger.warning(f"Skipping embedding process for {filename} because no text was extracted.")
        return

    # 1. Knowledge Graph Extraction (sinks data to Neo4j, returns triplets for enrichment)
    # ===================================================================================
    logger.info(f"Step 1: Extracting and storing knowledge graph for {filename}...")
    structured_data = await extract_knowledge_graph_from_text(extracted_text)
    if structured_data:
        await store_triplets_in_neo4j(structured_data)
    else:
        logger.info("No structured data extracted, proceeding with standard chunking.")

    # 2. Text Chunking
    # ==================
    logger.info(f"Step 2: Chunking document text for {filename}...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_text(extracted_text)
    logger.info(f"Split text into {len(chunks)} chunks.")

    # 3. Context Enrichment (The Core of the New Architecture)
    # ==========================================================
    logger.info(f"Step 3: Enriching {len(chunks)} chunks with graph context...")
    enriched_chunks = []
    for i, chunk in enumerate(chunks):
        enrichment_text = ""
        if structured_data:
            for head, _, relation, tail, _ in structured_data:
                # If a key entity from a triplet is in the chunk, add the fact.
                if str(head) in chunk or str(tail) in chunk:
                    enrichment_text += f"- Fakta: {head} -> {relation.replace('_', ' ').title()} -> {tail}\n"
        
        if enrichment_text:
            super_chunk = f"{chunk}\n\n[Fakta Terkait dari Graf Pengetahuan]:\n{enrichment_text}"
            enriched_chunks.append(super_chunk)
        else:
            enriched_chunks.append(chunk) # Use original chunk if no facts are relevant

    logger.info(f"Finished enriching chunks. Total enriched chunks: {len(enriched_chunks)}")

    # 4. Final Indexing into ChromaDB
    # =================================
    if not enriched_chunks:
        logger.warning(f"No chunks to index for {filename}. Aborting.")
        return

    logger.info(f"Step 4: Indexing {len(enriched_chunks)} enriched chunks into ChromaDB...")
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )
        collection = client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME, embedding_function=sentence_transformer_ef
        )

        # Create unique IDs and metadata for each chunk
        ids = [f"{filename}_{i}" for i in range(len(enriched_chunks))]
        metadatas = [{"source_document": filename} for _ in enriched_chunks]

        collection.add(documents=enriched_chunks, metadatas=metadatas, ids=ids)
        logger.info(f"Successfully indexed {len(enriched_chunks)} enriched chunks for {filename}.")
    except Exception as e:
        logger.error(f"Failed during ChromaDB indexing for {filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to index document: {str(e)}")
    # --- Guard Clause for Empty Text ---
    if not extracted_text or not extracted_text.strip():
        logger.warning(f"Skipping embedding process for {filename} because no text was extracted.")
        return
    # --- Knowledge Graph Extraction ---
    try:
        logger.info(f"Starting knowledge graph extraction for {filename}...")
        triplets = await extract_knowledge_graph_from_text(extracted_text)
        if triplets:
            await store_triplets_in_neo4j(triplets)
            logger.info(f"Successfully stored knowledge graph for {filename}.")
        else:
            logger.info(f"No triplets were extracted for {filename}, skipping graph storage.")
    except Exception as e:
        logger.error(f"An error occurred during knowledge graph processing for {filename}: {e}")
    
    # --- Vector Embedding and Storage ---
    logger.info(f"Starting vector embedding process for {filename}...")
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
    logger.info(f"Split text from '{filename}' into {len(chunks)} chunks.")

    # 3. Create metadata and unique IDs for each chunk
    metadatas = [{"source_document": filename} for _ in chunks]
    ids = [f"{filename}_chunk_{i}" for i, _ in enumerate(chunks)]
    logger.info(f"Generated {len(ids)} unique IDs and metadata entries.")

    # 4. Initialize ChromaDB Client
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    logger.info(f"ChromaDB client initialized at {CHROMA_PATH}.")

    # 5. Initialize Embedding Function
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )
    logger.info(f"Embedding function initialized with model: {EMBEDDING_MODEL_NAME}.")

    # 6. Get or Create Collection
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=sentence_transformer_ef,
        metadata={"hnsw:space": "cosine"}, # Use cosine distance
    )
    logger.info(f"Accessed or created collection: {CHROMA_COLLECTION_NAME}.")

    # 7. Add to Database
    collection.add(documents=chunks, metadatas=metadatas, ids=ids)
    logger.info(f"Successfully added {len(chunks)} document chunks for '{filename}' to the collection.")
