import logging
import google.generativeai as genai
import chromadb
from neo4j import GraphDatabase
from chromadb.utils import embedding_functions
from typing import List
from core.config import (
    GOOGLE_API_KEY,
    LLM_MODEL_NAME,
    EMBEDDING_MODEL_NAME,
    CHROMA_PATH,
    CHROMA_COLLECTION_NAME,
    NEO4J_URI,
    NEO4J_USERNAME,
    NEO4J_PASSWORD,
)

# Configure logging and AI model
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
genai.configure(api_key=GOOGLE_API_KEY)

async def vector_search_tool(query: str, filenames: List[str]) -> str:
    """
    Performs a vector search in ChromaDB filtered by filename.
    """
    logger.info(f"Executing vector search for query: '{query}' on files: {filenames}")
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )
        collection = client.get_collection(
            name=CHROMA_COLLECTION_NAME, embedding_function=sentence_transformer_ef
        )
        
        results = collection.query(
            query_texts=[query], 
            n_results=5, 
            where={"source_document": {"$in": filenames}}
        )
        
        if not results["documents"] or not results["documents"][0]:
            logger.info("Vector search returned no documents.")
            return ""
            
        vector_context = "\n\n".join(results["documents"][0])
        logger.info(f"Vector search completed. Context length: {len(vector_context)}")
        return vector_context
    except Exception as e:
        logger.error(f"Error during vector search: {e}", exc_info=True)
        return ""

async def graph_search_tool(query: str) -> str:
    """
    Generates a Cypher query from a question, executes it against Neo4j,
    and returns a formatted string of the results.
    """
    logger.info(f"Executing graph search for query: '{query}'")
    driver = None
    try:
        model = genai.GenerativeModel(LLM_MODEL_NAME)
        cypher_prompt = f"""
        Anda adalah ahli Cypher. Ubah pertanyaan berikut menjadi query Cypher untuk Neo4j.
        Skema Graph: Node memiliki label spesifik seperti :PERSON, :ROLE, :ORGANIZATION, dll. dan properti 'name'.
        Hanya kembalikan query-nya, tanpa penjelasan atau markdown.

        PENTING: Jaga agar semua nama entitas dan istilah (seperti jabatan atau nama lokasi) di dalam query Cypher SAMA PERSIS dengan yang ada di pertanyaan pengguna. JANGAN menerjemahkannya ke bahasa lain.

        Contoh:
        Pertanyaan: siapa manajer tefa?
        Query: MATCH (p:PERSON)-[]->(r:ROLE) WHERE r.name CONTAINS 'Manajer TEFA' RETURN p.name

        Pertanyaan: di mana sertifikat diterbitkan?
        Query: MATCH (d:DOCUMENT)-[:DITERBITKAN_DI]->(l:LOCATION) RETURN l.name
        
        Pertanyaan: {query}
        Query:
        """
        
        cypher_response = await model.generate_content_async(cypher_prompt)
        cypher_query = cypher_response.text.strip().replace('`', '').replace('cypher', '')
        logger.info(f"Generated Cypher query: {cypher_query}")

        if not cypher_query:
            logger.warning("LLM failed to generate a Cypher query.")
            return ""

        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        with driver.session() as session:
            result = session.run(cypher_query)
            graph_data = [record.data() for record in result]
            
            if not graph_data:
                logger.info("Graph search executed but returned no results.")
                return ""

            # Format graph results into a readable context
            formatted_graph_context = ""
            for record in graph_data:
                for key, value in record.items():
                    clean_key = key.split('.')[-1].replace('_', ' ').title()
                    formatted_graph_context += f"- {clean_key}: {value}\n"
            
            logger.info(f"Graph search successful. Context:\n{formatted_graph_context.strip()}")
            return formatted_graph_context.strip()
    except Exception as e:
        logger.error(f"Error during graph search: {e}", exc_info=True)
        return ""
    finally:
        if driver:
            driver.close()