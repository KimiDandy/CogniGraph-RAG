import json
import logging
import re
import time
from neo4j import AsyncGraphDatabase
from config import (
    GRAPH_EXTRACTION_PROMPT,
    NEO4J_MERGE_QUERY
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def extract_knowledge_graph_from_text(text: str, llm_model, max_retries: int = 3) -> list:
    """
    Mengekstrak entitas dan relasi dari teks menggunakan LLM dengan mekanisme coba lagi.

    Fungsi ini mengirimkan teks ke model generatif dan mencoba mem-parsing respons JSON.
    Jika parsing gagal, fungsi akan mencoba lagi dengan penundaan eksponensial.
    Ini juga menggunakan regex untuk mengekstrak JSON dari blok kode markdown secara andal.

    Args:
        text (str): Teks mentah untuk dianalisis.
        llm_model: Instansi model bahasa yang telah diinisialisasi.
        max_retries (int): Jumlah maksimum percobaan ulang jika terjadi kegagalan.

    Returns:
        list: Daftar triplet pengetahuan. Mengembalikan list kosong jika semua percobaan gagal.
    """
    if not text.strip():
        logger.info("Skipping knowledge graph extraction for empty text.")
        return []

    prompt = GRAPH_EXTRACTION_PROMPT.format(text=text)
    
    for attempt in range(max_retries):
        logger.info(f"Pinging LLM for knowledge graph extraction (Attempt {attempt + 1}/{max_retries})...")
        try:
            response = await llm_model.ainvoke(prompt)
            raw_response_text = response.content
            
            # Mencoba mengekstrak JSON dari dalam blok markdown
            json_match = re.search(r"```json\n(.*?)\n```", raw_response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Jika tidak ada blok markdown, asumsikan seluruh respons adalah JSON
                json_str = raw_response_text.strip()

            structured_data = json.loads(json_str)
            
            if not isinstance(structured_data, list):
                raise ValueError("Parsed JSON is not a list.")

            # Validasi bahwa data adalah list dari list dengan 5 elemen
            validated_data = [item for item in structured_data if isinstance(item, list) and len(item) == 5]
            
            if len(validated_data) != len(structured_data):
                logger.warning("Some items in the JSON response were malformed and have been filtered out.")

            logger.info(f"Successfully extracted and validated {len(validated_data)} structured items.")
            return validated_data

        except json.JSONDecodeError as e:
            logger.warning(f"Attempt {attempt + 1} failed: JSON decoding error. {e}")
            logger.debug(f"Raw response on failure: {raw_response_text}")
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed with an unexpected error: {e}", exc_info=True)
            logger.debug(f"Raw response on failure: {raw_response_text}")

        if attempt < max_retries - 1:
            sleep_time = 2 ** attempt  # Exponential backoff
            logger.info(f"Waiting for {sleep_time} seconds before retrying...")
            time.sleep(sleep_time)

    logger.error(f"Failed to extract or parse structured data after {max_retries} attempts.")
    return []


async def store_triplets_in_neo4j(driver: AsyncGraphDatabase.driver, structured_data: list, filename: str):
    """
    Menyimpan daftar triplet pengetahuan ke dalam database Neo4j.

    Fungsi ini melakukan iterasi pada setiap triplet, melakukan sanitasi pada
    label dan nama relasi agar sesuai dengan sintaks Cypher, dan menggunakan
    perintah `MERGE` untuk membuat node dan relasi secara idempoten.
    Setiap node juga diberikan properti `filename` untuk menjaga isolasi data
    antar dokumen.

    Args:
        structured_data (list): List berisi triplet pengetahuan.
        filename (str): Nama file asal data, untuk ditambahkan sebagai properti node.
    """
    if not structured_data:
        logger.info("No structured data to store.")
        return

    async with driver.session() as session:
        for head, head_label, relation, tail, tail_label in structured_data:
            # Menetapkan label default jika LLM gagal memberikannya untuk robustnes.
            head_label = head_label or 'ENTITY'
            tail_label = tail_label or 'ENTITY'

            # Sanitize labels and relation for Cypher
            head_label_safe = ''.join(c for c in head_label.upper() if c.isalnum())
            tail_label_safe = ''.join(c for c in tail_label.upper() if c.isalnum())
            relation_safe = ''.join(c for c in (relation or 'RELATED_TO').upper() if c.isalnum() or c == '_')

            if not all([head_label_safe, tail_label_safe, relation_safe]):
                continue
            
            # Use MERGE to create nodes with specific labels and their relationship
            query = NEO4J_MERGE_QUERY.format(
                head_label=head_label_safe,
                tail_label=tail_label_safe,
                relation=relation_safe
            )
            await session.run(query, head=str(head), tail=str(tail), filename=filename)
    logger.info(f"Successfully stored {len(structured_data)} relationships in Neo4j.")