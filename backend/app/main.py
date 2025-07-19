from fastapi import FastAPI, UploadFile, File, HTTPException
from ingestion.ocr_config import configure_tesseract
from pydantic import BaseModel
import shutil
from pathlib import Path
from ingestion.parser import parse_document
from ingestion.indexer import process_and_store_embeddings
from retrieval.hybrid_retriever import get_answer # Assuming execution from backend root
import logging
from fastapi.middleware.cors import CORSMiddleware

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Next RAG Backend")

@app.on_event("startup")
async def startup_event():
    configure_tesseract()

# Definisikan origin yang diizinkan (alamat frontend Anda)
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]

# Tambahkan CORS Middleware ke aplikasi Anda
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Izinkan semua metode (GET, POST, dll)
    allow_headers=["*"], # Izinkan semua header
)

# Define the base path for uploads relative to the backend root
UPLOAD_DIRECTORY = Path("data/uploads")

# Pydantic model for the query request
class QueryRequest(BaseModel):
    query: str
    filename: str

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...) ):
    """
    Accepts a file upload, saves it to a temporary location, 
    parses it to extract text, and returns the result.
    """
    # Ensure the upload directory exists
    UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    
    save_path = UPLOAD_DIRECTORY / file.filename
    logger.info(f"Receiving file: {file.filename}. Saving to: {save_path}")

    try:
        # Save the uploaded file to the specified directory
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Once saved, parse the document to extract text
        logger.info(f"File saved. Starting text extraction for {save_path}")
        extracted_text = await parse_document(file_path=str(save_path))

        # Check if parsing returned an error message
        if extracted_text.startswith("Error:"):
            logger.error(f"Failed to parse {file.filename}: {extracted_text}")
            raise HTTPException(status_code=422, detail=extracted_text)

        # If parsing is successful, proceed to chunk, embed, and index the text
        try:
            await process_and_store_embeddings(extracted_text, filename=file.filename)
            logger.info(f"Successfully indexed document: {file.filename}")
        except Exception as e:
            logger.error(f"Failed during embedding and indexing for {file.filename}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to index document: {str(e)}")

        return {
            "message": f"File '{file.filename}' processed, chunked, and embeddings stored successfully.",
            "filename": file.filename
        }

    except Exception as e:
        logger.error(f"An unexpected error occurred in the upload endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")
    finally:
        # It's good practice to close the file handle from UploadFile
        file.file.close()

@app.post("/query/")
async def answer_query(item: QueryRequest):
    """
    Receives a query, retrieves relevant context, and returns a generated answer.
    """
    try:
        logger.info(f"Received query for processing: {item.query}")
        answer = await get_answer(query=item.query, filename=item.filename)
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Error processing query '{item.query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")
