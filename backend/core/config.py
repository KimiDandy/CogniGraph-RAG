import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Google API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Nama model LLM dari Google AI Studio
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash")

# Neo4j Database Configuration
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Path ke Tesseract OCR executable.
# Pengguna harus memverifikasi path ini sesuai dengan instalasi di mesin mereka.
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Nama model embedding dari Hugging Face
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"

# Path untuk menyimpan database vektor ChromaDB secara lokal
CHROMA_PATH = "data/chromadb"

# Nama koleksi di dalam ChromaDB
CHROMA_COLLECTION_NAME = "rag_collection"
