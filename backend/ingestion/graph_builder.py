import json
import logging
import re
import time
from neo4j import AsyncGraphDatabase
from config import (
    GRAPH_EXTRACTION_PROMPT,
    NEO4J_MERGE_QUERY
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def extract_knowledge_graph_from_text(text: str, llm_model, max_retries: int = 3) -> list:
    """
    Mengekstrak triplet pengetahuan (entitas-relasi-entitas) dari teks mentah menggunakan LLM.

    Fungsi ini dirancang untuk tangguh (robust) terhadap kemungkinan kegagalan API LLM atau
    respons yang tidak terduga. Ia menggunakan mekanisme coba lagi (retry) dengan penundaan
    eksponensial dan secara proaktif mencoba membersihkan respons LLM untuk mengekstrak JSON.

    Args:
        text (str): Teks mentah yang akan dianalisis.
        llm_model: Instance model bahasa yang telah diinisialisasi.
        max_retries (int): Jumlah maksimum percobaan ulang jika terjadi kegagalan.

    Returns:
        list: Daftar triplet pengetahuan. Mengembalikan list kosong jika semua percobaan gagal.
    """
    if not text.strip():
        logger.info("Teks kosong, proses ekstraksi knowledge graph dilewati.")
        return []

    prompt = GRAPH_EXTRACTION_PROMPT.format(text=text)
    
    for attempt in range(max_retries):
        logger.info(f"Menghubungi LLM untuk ekstraksi graph (Percobaan {attempt + 1}/{max_retries})...")
        try:
            response = await llm_model.ainvoke(prompt)
            raw_response_text = response.content
            
            json_match = re.search(r"```json\n(.*?)\n```", raw_response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = raw_response_text.strip()

            structured_data = json.loads(json_str)
            
            if not isinstance(structured_data, list):
                raise ValueError("Struktur JSON yang di-parse bukan sebuah list.")

            validated_data = [item for item in structured_data if isinstance(item, list) and len(item) == 5]
            
            if len(validated_data) != len(structured_data):
                logger.warning("Beberapa item dalam respons JSON tidak sesuai format dan telah disaring.")

            logger.info(f"Berhasil mengekstrak dan memvalidasi {len(validated_data)} triplet pengetahuan.")
            return validated_data

        except json.JSONDecodeError:
            logger.warning(f"Percobaan {attempt + 1} gagal: Gagal mem-parsing JSON dari respons LLM.")
            logger.debug(f"Respons mentah saat gagal: {raw_response_text}")
        except Exception as e:
            logger.error(f"Percobaan {attempt + 1} gagal dengan kesalahan tak terduga: {e}", exc_info=True)
            logger.debug(f"Respons mentah saat gagal: {raw_response_text}")

        if attempt < max_retries - 1:
            sleep_time = 2 ** attempt
            logger.info(f"Menunggu {sleep_time} detik sebelum mencoba lagi...")
            time.sleep(sleep_time)

    logger.error(f"Gagal mengekstrak data terstruktur setelah {max_retries} percobaan.")
    return []


async def store_triplets_in_neo4j(driver: AsyncGraphDatabase.driver, structured_data: list, filename: str):
    """
    Menyimpan triplet pengetahuan yang telah diekstrak ke dalam database Neo4j secara idempoten.

    Fungsi ini menggunakan perintah `MERGE` dalam Cypher. Tujuannya adalah untuk membuat node
    dan relasi hanya jika mereka belum ada. Ini mencegah duplikasi data jika dokumen yang
    sama diproses ulang. Properti `filename` ditambahkan untuk isolasi data antar dokumen.

    Args:
        driver: Instance driver Neo4j yang aktif.
        structured_data (list): List berisi triplet pengetahuan yang akan disimpan.
        filename (str): Nama file asal data, untuk ditambahkan sebagai properti node.
    """
    if not structured_data:
        logger.info("Tidak ada data terstruktur untuk disimpan ke Neo4j.")
        return

    async with driver.session() as session:
        for head, head_label, relation, tail, tail_label in structured_data:
            head_label = head_label or 'ENTITY'
            tail_label = tail_label or 'ENTITY'
            head_label_safe = ''.join(c for c in head_label.upper() if c.isalnum())
            tail_label_safe = ''.join(c for c in tail_label.upper() if c.isalnum())
            relation_safe = ''.join(c for c in (relation or 'RELATED_TO').upper() if c.isalnum() or c == '_')

            if not all([head_label_safe, tail_label_safe, relation_safe]):
                continue
            
            query = NEO4J_MERGE_QUERY.format(
                head_label=head_label_safe,
                tail_label=tail_label_safe,
                relation=relation_safe
            )
            await session.run(query, head=str(head), tail=str(tail), filename=filename)
    logger.info(f"Berhasil menyimpan {len(structured_data)} relasi dari '{filename}' ke Neo4j.")