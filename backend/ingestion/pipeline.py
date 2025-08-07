import logging
import shutil
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ingestion.parser import parse_document
from ingestion.graph_builder import extract_knowledge_graph_from_text, store_triplets_in_neo4j
from ingestion.indexer import index_documents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_document(file_path: str, neo4j_driver, chroma_client, embedding_function, llm_model):
    """
    Orkestrasi pipeline ingesti dokumen secara lengkap.

    Fungsi ini menjalankan pipeline Graph-Enhanced RAG:
    1.  Mem-parsing teks dari file (termasuk OCR jika diperlukan).
    2.  Ekstraksi Knowledge Graph: Mengekstrak entitas dan relasi dari teks
        menggunakan LLM dan menyimpannya ke Neo4j.
    3.  Text Chunking: Memecah teks menjadi potongan-potongan yang lebih kecil.
    4.  Pengayaan Konteks: Menambahkan fakta-fakta relevan dari knowledge graph
        ke setiap potongan teks untuk memberikan konteks tambahan.
    5.  Indexing: Memanggil fungsi untuk mengindeks potongan yang telah diperkaya ke ChromaDB.

    Args:
        file_path (str): Path absolut ke file yang akan diproses.
    """
    filename = Path(file_path).name
    try:
        logger.info(f"Memulai pemrosesan dokumen untuk: {file_path}")
        
        # Langkah 1: Parsing Dokumen
        text_content = await parse_document(file_path)
        if not text_content or not text_content.strip():
            logger.warning(f"Gagal mengekstrak teks atau teks kosong untuk {filename}. Proses dihentikan.")
            return

        # Langkah 2: Ekstraksi dan Penyimpanan Knowledge Graph
        logger.info(f"Ekstraksi knowledge graph untuk {filename}...")
        try:
            structured_data = await extract_knowledge_graph_from_text(text_content, llm_model=llm_model)
            if structured_data:
                await store_triplets_in_neo4j(driver=neo4j_driver, structured_data=structured_data, filename=filename)
            else:
                logger.info("Tidak ada data terstruktur yang diekstrak, melanjutkan dengan chunking standar.")
        except Exception as e:
            logger.error(f"Gagal saat pemrosesan knowledge graph untuk {filename}: {e}", exc_info=True)
            structured_data = None # Lanjutkan tanpa pengayaan graf jika gagal

        # Langkah 3: Pemecahan Teks (Chunking)
        logger.info(f"Memecah teks dokumen untuk {filename}...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_text(text_content)
        logger.info(f"Teks dipecah menjadi {len(chunks)} potongan.")

        # Langkah 4: Pengayaan Potongan Teks
        logger.info(f"Memperkaya {len(chunks)} potongan teks dengan konteks dari graph...")
        enriched_chunks = []
        if structured_data:
            for chunk in chunks:
                enrichment_text = ""
                for head, _, relation, tail, _ in structured_data:
                    if str(head) in chunk or str(tail) in chunk:
                        enrichment_text += f"- Fakta: {head} -> {relation.replace('_', ' ').title()} -> {tail}\n"
                
                if enrichment_text:
                    enriched_chunks.append(f"{chunk}\n\n[Fakta Terkait dari Knowledge Graph]:\n{enrichment_text}")
                else:
                    enriched_chunks.append(chunk)
        else:
            enriched_chunks = chunks # Gunakan chunk asli jika tidak ada data graf

        logger.info(f"Selesai memperkaya potongan. Total potongan diperkaya: {len(enriched_chunks)}")

        # Langkah 5: Pengindeksan ke ChromaDB
        ids = [f"{filename}_{i}" for i in range(len(enriched_chunks))]
        metadatas = [{"source_document": filename} for _ in enriched_chunks]
        
        await index_documents(
            chroma_client=chroma_client,
            embedding_function=embedding_function,
            documents=enriched_chunks,
            metadatas=metadatas,
            ids=ids,
            filename=filename
        )
        
        logger.info(f"Berhasil memproses dan mengindeks {filename}")

    except Exception as e:
        logger.error(f"Error dalam pipeline pemrosesan untuk {filename}: {e}", exc_info=True)
        raise e
