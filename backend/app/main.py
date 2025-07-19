from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
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
    filename: str
    text_content: str # This is sent by the frontend but not used in the reverted logic
    history: Optional[List[Dict[str, str]]] = None # Kept for model compatibility, but will be ignored

@app.on_event("startup")
async def startup_event():
    configure_tesseract()

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    filename = file.filename
    sanitized_filename = Path(filename).name
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / sanitized_filename

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        logger.info(f"File '{sanitized_filename}' saved. Starting synchronous processing...")
        
        # Process the document directly and wait for it to finish
        await process_document(str(file_path))
        
        logger.info(f"Successfully processed and indexed {sanitized_filename}")
        return {"filename": sanitized_filename, "message": "File processed and indexed successfully."}

    except Exception as e:
        logger.error(f"Error during file processing for {sanitized_filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not save or process file: {str(e)}")

@app.post("/query/")
async def answer_query(item: QueryRequest):
    """
    Receives a query, retrieves context, and returns an answer.
    (Conversational logic has been removed as per user request).
    """
    try:
        logger.info(f"Received query: '{item.query}' for document: '{item.filename}'")
        
        # Get the answer using the original question, ignoring chat history.
        answer = await get_answer(query=item.query, filename=item.filename)
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Error processing query '{item.query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")
