import sys
import shutil
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
from .schemas import QueryRequest

from loguru import logger
from neo4j import AsyncGraphDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
import chromadb
from chromadb.utils import embedding_functions


from config import (
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD,
    CHROMA_DB_PATH, LLM_MODEL_NAME, GOOGLE_API_KEY, EMBEDDING_MODEL_NAME
)
from ingestion.pipeline import process_document
from retrieval.hybrid_retriever import get_answer
from ingestion.ocr_config import configure_tesseract

logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/backend.log", rotation="10 MB", level="DEBUG")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Mengelola siklus hidup aplikasi (startup dan shutdown) secara terpusat.

    Penggunaan `lifespan` adalah praktik terbaik di FastAPI untuk memastikan bahwa
    sumber daya seperti koneksi database dan model AI diinisialisasi sekali saat
    startup dan dibersihkan dengan benar saat shutdown. Ini mencegah kebocoran
    sumber daya dan memastikan aplikasi selalu dalam keadaan siap.
    """
    logger.info("Startup Aplikasi: Menginisialisasi semua sumber daya...")
    try:
        # 1. Konfigurasi Tesseract OCR
        configure_tesseract()
        logger.info("Konfigurasi Tesseract OCR berhasil.")

        # 2. Inisialisasi Driver Neo4j
        app.state.neo4j_driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        await app.state.neo4j_driver.verify_connectivity()
        logger.info("Driver Neo4j berhasil diinisialisasi dan koneksi terverifikasi.")

        # 3. Inisialisasi Klien ChromaDB
        app.state.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        logger.info(f"Klien ChromaDB diinisialisasi dari path: {CHROMA_DB_PATH}")

        # 4. Inisialisasi Model AI
        app.state.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL_NAME)
        app.state.chat_model = ChatGoogleGenerativeAI(model=LLM_MODEL_NAME, google_api_key=GOOGLE_API_KEY, temperature=0.1)
        logger.info("Model AI (Embedding dan Chat) berhasil diinisialisasi.")

    except Exception as e:
        logger.critical(f"GAGAL TOTAL SAAT STARTUP: {e}", exc_info=True)
        # Reset state jika terjadi kegagalan untuk mencegah kondisi tidak menentu
        app.state.neo4j_driver = None
        app.state.chroma_client = None
        app.state.embedding_function = None
        app.state.chat_model = None

    yield

    logger.info("Shutdown Aplikasi: Menutup koneksi dan membersihkan sumber daya...")
    if hasattr(app.state, 'neo4j_driver') and app.state.neo4j_driver:
        await app.state.neo4j_driver.close()
        logger.info("Koneksi driver Neo4j berhasil ditutup.")
    logger.info("Pembersihan sumber daya selesai.")

app = FastAPI(title="CogniGraph RAG API", lifespan=lifespan)

origins = ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/uploadfile/", summary="Unggah dan Proses Dokumen")
async def create_upload_file(request: Request, file: UploadFile, background_tasks: BackgroundTasks):
    """
    Menerima unggahan file, menyimpannya, dan memulai proses ingesti di latar belakang.

    Proses ingesti (parsing, ekstraksi graph, vektorisasi) adalah operasi yang intensif.
    Dengan menjalankannya sebagai background task, endpoint ini dapat segera mengembalikan
    respons ke klien tanpa harus menunggu seluruh proses selesai.

    Args:
        request (Request): Objek request FastAPI.
        file (UploadFile): File yang diunggah oleh pengguna.
        background_tasks (BackgroundTasks): Mekanisme FastAPI untuk tugas latar belakang.

    Returns:
        dict: Konfirmasi bahwa file telah diterima dan proses dimulai.
    """
    # Sanitasi nama file untuk keamanan, hanya menggunakan nama file dasar.
    sanitized_filename = Path(file.filename).name
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / sanitized_filename

    try:
        # Menyimpan file yang diunggah ke direktori lokal.
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File '{sanitized_filename}' berhasil disimpan di '{file_path}'")

        # Menjadwalkan tugas ingesti dokumen untuk berjalan di latar belakang.
        # Semua state yang dibutuhkan (koneksi DB, model) diambil dari app.state.
        background_tasks.add_task(
            process_document,
            file_path=str(file_path),
            neo4j_driver=request.app.state.neo4j_driver,
            chroma_client=request.app.state.chroma_client,
            embedding_function=request.app.state.embedding_function,
            llm_model=request.app.state.chat_model
        )
        
        logger.info(f"Proses ingesti untuk '{sanitized_filename}' telah dijadwalkan.")
        return {"filename": sanitized_filename, "message": "File berhasil diunggah dan proses ingesti telah dimulai."}

    except Exception as e:
        logger.error(f"Gagal saat mengunggah atau menjadwalkan proses untuk '{sanitized_filename}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Tidak dapat menyimpan atau memproses file: {str(e)}")

@app.post("/query/", summary="Ajukan Pertanyaan ke Dokumen")
async def answer_query(request: Request, item: QueryRequest):
    """
    Endpoint utama untuk menjawab pertanyaan pengguna berdasarkan dokumen yang dipilih.

    Menerima kueri, daftar nama file, dan riwayat percakapan, lalu memanggil
    orkestrator RAG (`get_answer`) untuk menghasilkan jawaban.

    Args:
        request (Request): Objek request FastAPI.
        item (QueryRequest): Data permintaan yang divalidasi oleh Pydantic.

    Returns:
        dict: Jawaban yang dihasilkan oleh alur RAG.
    """
    try:
        logger.info(f"Menerima kueri: '{item.query}' pada dokumen: {item.filenames}")
        
        # Memanggil fungsi orkestrator utama dengan state yang diperlukan dari aplikasi.
        answer = await get_answer(
            query=item.query,
            filenames=item.filenames,
            chat_history=item.chat_history,
            chat_model=request.app.state.chat_model,
            chroma_client=request.app.state.chroma_client,
            embedding_function=request.app.state.embedding_function
        )
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Gagal memproses kueri '{item.query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal saat memproses permintaan Anda.")
