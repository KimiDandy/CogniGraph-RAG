import google.generativeai as genai
import json
import logging
from neo4j import GraphDatabase
from core.config import (
    GOOGLE_API_KEY,
    LLM_MODEL_NAME,
    NEO4J_URI,
    NEO4J_USERNAME,
    NEO4J_PASSWORD,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure the generative AI model
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    logger.error(f"Failed to configure Google AI SDK: {e}")

async def extract_knowledge_graph_from_text(text: str) -> list:
    """
    Extracts entities, labels, and relationships from text using an LLM.
    Returns them as a list of 5-element tuples: [head, head_label, relation, tail, tail_label].
    """
    if not text.strip():
        logger.info("Skipping knowledge graph extraction for empty text.")
        return []

    model = genai.GenerativeModel(LLM_MODEL_NAME)

    prompt = f"""
    Anda adalah ahli dalam Information Extraction. Dari teks di bawah ini, ekstrak semua entitas penting dan hubungan di antaranya.
    Tugas Anda adalah mengidentifikasi Subjek, Label Subjek, Hubungan, Objek, dan Label Objek.
    Label yang valid adalah: 'PERSON', 'ORGANIZATION', 'ROLE', 'PROJECT', 'LOCATION', 'DATE', 'DOCUMENT'.

    Format output Anda HARUS berupa sebuah string JSON yang valid, berisi sebuah list dari list.
    Setiap list di dalamnya harus memiliki 5 elemen: [subjek, label_subjek, hubungan, objek, label_objek].

    Contoh:
    Teks: "Dalam proyek Presensi Face Recognition, Kimi Dandy Yudanarko adalah seorang Peserta. Sertifikat ini ditandatangani oleh Ely Mulyadi, Manajer TEFA JTI Innovation di Jember pada 29 Juni 2025."
    JSON Output:
    [
        ["Kimi Dandy Yudanarko", "PERSON", "ADALAH_SEORANG", "Peserta", "ROLE"],
        ["Ely Mulyadi", "PERSON", "MEMILIKI_JABATAN", "Manajer TEFA JTI Innovation", "ROLE"],
        ["Sertifikat", "DOCUMENT", "DITANDATANGANI_OLEH", "Ely Mulyadi", "PERSON"],
        ["Sertifikat", "DITERBITKAN_DI", "Jember", "LOCATION"],
        ["Sertifikat", "DITERBITKAN_PADA", "29 Juni 2025", "DATE"]
    ]

    PENTING: Pastikan untuk mengekstrak nama lengkap dan jabatan selengkap mungkin. Hanya gunakan label yang telah ditentukan.

    Teks untuk dianalisis:
    ---
    {text}
    ---

    JSON Output:
    """

    logger.info("Pinging LLM for structured knowledge graph extraction...")
    try:
        response = await model.generate_content_async(prompt)
        cleaned_response = response.text.strip().replace('`', '').replace('json', '')
        structured_data = json.loads(cleaned_response)
        
        # Validate that the data is a list of lists with 5 elements each
        validated_data = [item for item in structured_data if isinstance(item, list) and len(item) == 5]
        
        logger.info(f"Successfully extracted {len(validated_data)} structured items.")
        return validated_data
    except Exception as e:
        logger.error(f"Failed to extract or parse structured data from LLM response: {e}", exc_info=True)
        logger.error(f"Raw response was: {response.text if 'response' in locals() else 'No response'}")
        return []

async def store_triplets_in_neo4j(structured_data: list):
    """
    Stores a list of structured data [head, head_label, relation, tail, tail_label] into Neo4j.
    """
    if not structured_data:
        logger.info("No structured data to store.")
        return

    driver = None
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        with driver.session() as session:
            for head, head_label, relation, tail, tail_label in structured_data:
                # Sanitize labels and relation for Cypher
                head_label_safe = ''.join(c for c in head_label.upper() if c.isalnum())
                tail_label_safe = ''.join(c for c in tail_label.upper() if c.isalnum())
                relation_safe = ''.join(c for c in relation.upper() if c.isalnum() or c == '_')

                if not all([head_label_safe, tail_label_safe, relation_safe]):
                    continue
                
                # Use MERGE to create nodes with specific labels and their relationship
                query = (
                    f"MERGE (h:{head_label_safe} {{name: $head}}) "
                    f"MERGE (t:{tail_label_safe} {{name: $tail}}) "
                    f"MERGE (h)-[:`{relation_safe}`]->(t)"
                )
                session.run(query, head=str(head), tail=str(tail))
        logger.info(f"Successfully stored {len(structured_data)} relationships in Neo4j.")
    except Exception as e:
        logger.error(f"Failed to store structured data in Neo4j: {e}", exc_info=True)
    finally:
        if driver:
            driver.close()