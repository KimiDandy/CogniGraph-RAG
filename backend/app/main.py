from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from pydantic import BaseModel
import shutil
from pathlib import Path
from ingestion.pipeline import process_document
from ingestion.ocr_config import configure_tesseract
from retrieval.hybrid_retriever import get_answer
import logging
from fastapi.middleware.cors import CORSMiddleware

from typing import Optional, List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CogniGraph RAG API")

origins = ["http://localhost:3000", "http://localhost:3001"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StatusResponse(BaseModel):
    status: str
    message: Optional[str] = None
    text_content: Optional[str] = None

class QueryRequest(BaseModel):
    query: str
    filenames: List[str]
    chat_history: Optional[List[Dict[str, str]]] = None

@app.on_event("startup")
async def startup_event():
    """Mengonfigurasi Tesseract OCR saat aplikasi dimulai."""
    configure_tesseract()

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile, background_tasks: BackgroundTasks):
    """
    Menerima, menyimpan, dan memproses file dokumen yang diunggah.

    Fungsi ini menangani unggahan file, menyimpannya ke direktori lokal,
    dan kemudian memicu pipeline pemrosesan dokumen secara sinkron.

    Args:
        file (UploadFile): File yang diunggah oleh pengguna, sesuai dengan standar FastAPI.

    Returns:
        dict: Konfirmasi bahwa file telah berhasil diproses dan diindeks.
    
    Raises:
        HTTPException: Jika terjadi kesalahan saat menyimpan atau memproses file.
    """
    filename = file.filename
    sanitized_filename = Path(filename).name
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / sanitized_filename

    try:
        # Simpan file ke disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File '{sanitized_filename}' saved to '{file_path}'")

        # Jadwalkan pemrosesan dokumen sebagai tugas latar belakang
        background_tasks.add_task(process_document, str(file_path))
        
        logger.info(f"Processing for {sanitized_filename} has been started in the background.")
        return {"filename": sanitized_filename, "message": "File upload successful. Processing has started in the background."}

    except Exception as e:
        logger.error(f"Error during file processing for {sanitized_filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not save or process file: {str(e)}")

@app.post("/query/")
async def answer_query(item: QueryRequest):
    """
    Menerima kueri, mengambil konteks dari dokumen, dan mengembalikan jawaban.

    Endpoint ini menggunakan logika RAG untuk menjawab pertanyaan pengguna
    berdasarkan konten dari file yang ditentukan dan riwayat percakapan.

    Args:
        item (QueryRequest): Objek yang berisi kueri, daftar nama file,
                             dan riwayat percakapan (opsional).

    Returns:
        dict: Jawaban yang dihasilkan oleh sistem RAG.

    Raises:
        HTTPException: Jika terjadi kesalahan selama pemrosesan kueri.
    """
    try:
        logger.info(f"Received query: '{item.query}' for documents: {item.filenames}")
        
        answer = await get_answer(query=item.query, filenames=item.filenames, chat_history=item.chat_history)
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Error processing query '{item.query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")
