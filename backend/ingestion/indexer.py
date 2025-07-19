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
    Memproses teks, membangun knowledge graph, dan mengindeksnya ke ChromaDB.

    Fungsi ini menjalankan pipeline Graph-Enhanced RAG:
    1.  **Ekstraksi Knowledge Graph:** Mengekstrak entitas dan relasi dari teks
        menggunakan LLM dan menyimpannya ke Neo4j.
    2.  **Text Chunking:** Memecah teks menjadi potongan-potongan yang lebih kecil.
    3.  **Pengayaan Konteks:** Menambahkan fakta-fakta relevan dari knowledge graph
        ke setiap potongan teks untuk memberikan konteks tambahan.
    4.  **Indexing:** Membuat embedding dari potongan teks yang telah diperkaya dan
        menyimpannya ke dalam database vektor ChromaDB.

    Args:
        extracted_text (str): Teks mentah yang diekstrak dari dokumen.
        filename (str): Nama file asli, digunakan untuk metadata.
    """
    if not extracted_text or not extracted_text.strip():
        logger.warning(f"Skipping embedding process for {filename} because no text was extracted.")
        return

    logger.info(f"Langkah 1: Ekstraksi dan penyimpanan knowledge graph untuk {filename}...")
    try:
        structured_data = await extract_knowledge_graph_from_text(extracted_text)
        if structured_data:
            await store_triplets_in_neo4j(structured_data, filename=filename)
        else:
            logger.info("No structured data extracted, proceeding with standard chunking.")
    except Exception as e:
        logger.error(f"Failed during knowledge graph processing for {filename}: {e}", exc_info=True)
        # Continue without graph enrichment if this step fails
        structured_data = None

    logger.info(f"Langkah 2: Memecah teks dokumen untuk {filename}...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_text(extracted_text)
    logger.info(f"Split text into {len(chunks)} chunks.")

    logger.info(f"Langkah 3: Memperkaya {len(chunks)} potongan teks dengan konteks dari graph...")
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

    if not enriched_chunks:
        logger.warning(f"Tidak ada potongan teks untuk diindeks untuk file {filename}. Proses dibatalkan.")
        return

    logger.info(f"Langkah 4: Mengindeks {len(enriched_chunks)} potongan teks ke ChromaDB...")
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
