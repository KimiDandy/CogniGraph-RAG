import sys
import shutil
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict

from loguru import logger
from neo4j import AsyncGraphDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
import chromadb
from chromadb.utils import embedding_functions

# Import configurations and core components
from config import (
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD,
    CHROMA_DB_PATH, LLM_MODEL_NAME, GOOGLE_API_KEY, EMBEDDING_MODEL_NAME
)
from ingestion.pipeline import process_document
from retrieval.hybrid_retriever import get_answer
from ingestion.ocr_config import configure_tesseract

# --- Loguru Configuration ---
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/backend.log", rotation="10 MB", level="DEBUG")

# --- Lifespan for Resource Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application Startup: Initializing resources...")
    try:
        # 1. Configure Tesseract OCR
        configure_tesseract()
        logger.info("Tesseract OCR configured.")

        # 2. Initialize Neo4j Driver
        app.state.neo4j_driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        await app.state.neo4j_driver.verify_connectivity()
        logger.info("Neo4j driver initialized and connection verified.")

        # 3. Initialize ChromaDB Client
        app.state.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        logger.info(f"ChromaDB client initialized from path: {CHROMA_DB_PATH}")

        # 4. Initialize AI Models
        app.state.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL_NAME)
        app.state.chat_model = ChatGoogleGenerativeAI(model=LLM_MODEL_NAME, google_api_key=GOOGLE_API_KEY, temperature=0.1)
        logger.info("Google AI models (Embedding and Chat) initialized.")

    except Exception as e:
        logger.critical(f"FATAL STARTUP ERROR: {e}", exc_info=True)
        # Reset states on failure
        app.state.neo4j_driver = None
        app.state.chroma_client = None
        app.state.embedding_function = None
        app.state.chat_model = None

    yield

    logger.info("Application Shutdown: Cleaning up resources...")
    if hasattr(app.state, 'neo4j_driver') and app.state.neo4j_driver:
        await app.state.neo4j_driver.close()
        logger.info("Neo4j driver connection closed.")
    logger.info("Resource cleanup complete.")

# --- FastAPI App Initialization ---
app = FastAPI(title="CogniGraph RAG API", lifespan=lifespan)

# CORS Middleware
origins = ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models for API ---
class QueryRequest(BaseModel):
    query: str
    filenames: List[str]
    chat_history: Optional[List[Dict[str, str]]] = None

# --- API Endpoints ---
@app.post("/uploadfile/")
async def create_upload_file(request: Request, file: UploadFile, background_tasks: BackgroundTasks):
    filename = file.filename
    sanitized_filename = Path(filename).name
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / sanitized_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File '{sanitized_filename}' saved to '{file_path}'")

        # Pass state objects to the background task
        background_tasks.add_task(
            process_document,
            file_path=str(file_path),
            neo4j_driver=request.app.state.neo4j_driver,
            chroma_client=request.app.state.chroma_client,
            embedding_function=request.app.state.embedding_function,
            llm_model=request.app.state.chat_model
        )
        
        logger.info(f"Processing for {sanitized_filename} started in the background.")
        return {"filename": sanitized_filename, "message": "File upload successful. Processing has started."}

    except Exception as e:
        logger.error(f"Error during file upload for {sanitized_filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not save or process file: {str(e)}")

@app.post("/query/")
async def answer_query(request: Request, item: QueryRequest):
    try:
        logger.info(f"Received query: '{item.query}' for documents: {item.filenames}")
        
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
        logger.error(f"Error processing query '{item.query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")
