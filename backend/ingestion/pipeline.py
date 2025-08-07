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
    Mengorkestrasi pipeline ingesti dokumen dari awal hingga akhir.

    Fungsi ini adalah jantung dari proses ingesti data, menjalankan alur
    Graph-Enhanced RAG (GE-RAG) untuk mengubah dokumen mentah menjadi
    pengetahuan yang terstruktur dan terindeks.

    Alur Proses:
    1. Parsing: Mengekstrak teks bersih dari file, dengan dukungan OCR.
    2. Ekstraksi Graph: Menggunakan LLM untuk mengidentifikasi entitas dan relasi,
       membangun Knowledge Graph yang disimpan di Neo4j.
    3. Chunking: Memecah teks menjadi potongan-potongan logis untuk diindeks.
    4. Pengayaan Konteks: Menyuntikkan relasi dari Knowledge Graph ke dalam
       setiap potongan teks yang relevan, memberikan konteks yang lebih kaya.
    5. Indeksasi: Melakukan vektorisasi pada potongan yang telah diperkaya dan
       menyimpannya ke dalam ChromaDB untuk pencarian semantik.

    Args:
        file_path (str): Path absolut ke file yang akan diproses.
        neo4j_driver: Instance driver Neo4j yang aktif.
        chroma_client: Instance klien ChromaDB yang aktif.
        embedding_function: Fungsi embedding yang akan digunakan.
        llm_model: Model bahasa yang akan digunakan untuk ekstraksi.
    """
    filename = Path(file_path).name
    try:
        logger.info(f"Memulai pipeline ingesti untuk '{filename}'...")
        
        # --- Fase 1: Parsing Dokumen ---
        text_content = await parse_document(file_path)
        if not text_content or not text_content.strip():
            logger.warning(f"Teks tidak ditemukan atau kosong untuk '{filename}'. Pipeline dihentikan untuk file ini.")
            return

        # --- Fase 2: Ekstraksi dan Penyimpanan Knowledge Graph ---
        logger.info(f"Memulai ekstraksi knowledge graph untuk '{filename}'...")
        structured_data = None
        try:
            structured_data = await extract_knowledge_graph_from_text(text_content, llm_model=llm_model)
            if structured_data:
                await store_triplets_in_neo4j(driver=neo4j_driver, structured_data=structured_data, filename=filename)
            else:
                logger.info(f"Tidak ada data terstruktur yang diekstrak untuk '{filename}'. Melanjutkan dengan teks asli.")
        except Exception as e:
            logger.error(f"Gagal saat ekstraksi knowledge graph untuk '{filename}': {e}. Proses ingesti tetap dilanjutkan.", exc_info=True)

        # --- Fase 3: Pemecahan Teks (Chunking) ---
        logger.info(f"Memecah teks dari '{filename}' menjadi beberapa potongan (chunks)...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,    
            chunk_overlap=200,  
            length_function=len,
        )
        chunks = text_splitter.split_text(text_content)
        logger.info(f"Teks berhasil dipecah menjadi {len(chunks)} potongan.")

        # --- Fase 4: Pengayaan Potongan Teks dengan Konteks Graf ---
        enriched_chunks = chunks
        if structured_data:
            logger.info(f"Memperkaya {len(chunks)} potongan teks dengan konteks dari knowledge graph...")
            temp_enriched_chunks = []
            for chunk in chunks:
                enrichment_text = ""
                for head, _, relation, tail, _ in structured_data:
                    if str(head) in chunk or str(tail) in chunk:
                        enrichment_text += f"- Fakta Terkait: {head} -> {relation.replace('_', ' ').title()} -> {tail}\n"
                
                if enrichment_text:
                    temp_enriched_chunks.append(f"{chunk}\n\n[Konteks dari Knowledge Graph]:\n{enrichment_text}")
                else:
                    temp_enriched_chunks.append(chunk)
            enriched_chunks = temp_enriched_chunks
            logger.info(f"Pengayaan konteks selesai. Total potongan diperkaya: {len(enriched_chunks)}")

        # --- Fase 5: Pengindeksan ke Vector Store ---
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
        
        logger.info(f"Pipeline ingesti untuk '{filename}' selesai dengan sukses.")

    except Exception as e:
        logger.error(f"Terjadi kesalahan fatal dalam pipeline untuk '{filename}': {e}", exc_info=True)
        raise e
