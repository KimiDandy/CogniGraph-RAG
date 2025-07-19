from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Path
from ingestion.ocr_config import configure_tesseract
from pydantic import BaseModel
import shutil
import pathlib
from ingestion.pipeline import process_document
from retrieval.hybrid_retriever import get_answer
import logging
from fastapi.middleware.cors import CORSMiddleware
from retrieval.conversational_logic import rephrase_question_with_history
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

# In-memory storage for task status and results
processing_status = {}

class StatusResponse(BaseModel):
    status: str
    message: Optional[str] = None
    text_content: Optional[str] = None

class QueryRequest(BaseModel):
    query: str
    filename: str
    history: Optional[List[Dict[str, str]]] = None

@app.on_event("startup")
async def startup_event():
    configure_tesseract()

@app.post("/uploadfile/")
async def create_upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...) ):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file name provided")

    safe_filename = file.filename.replace(" ", "_")
    upload_dir = pathlib.Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / safe_filename

    # Save the file immediately
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    # Set initial status
    processing_status[safe_filename] = {"status": "processing", "message": "Upload successful, starting processing..."}
    
    # Run the processing in the background with the file path
    background_tasks.add_task(process_document, str(file_path), safe_filename, processing_status)

    return {"filename": safe_filename, "message": f"File '{safe_filename}' uploaded. Processing in background."}

@app.get("/status/{filename}", response_model=StatusResponse)
async def get_status(filename: str = Path(..., description="The name of the file to check status for")):
    status = processing_status.get(filename, {"status": "not_found", "message": "File not found."})
    return status

@app.post("/query/")
async def answer_query(item: QueryRequest):
    """
    Receives a query, rephrases it based on history, retrieves context, and returns an answer.
    """
    try:
        logger.info(f"Received query: '{item.query}' for document: '{item.filename}' with history.")
        
        # Rephrase the question to be standalone
        standalone_question = await rephrase_question_with_history(item.query, item.history or [])
        
        # Get the answer using the rephrased, standalone question
        answer = await get_answer(query=standalone_question, filename=item.filename)
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Error processing query '{item.query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")
