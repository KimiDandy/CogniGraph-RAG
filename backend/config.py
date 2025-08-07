import os
import logging
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Google Gemini API Key ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY not found in environment variables. Please create a .env file and set it.")

# --- Neo4j Database Credentials ---
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
    logger.warning("Neo4j credentials not found in environment variables. Please check your .env file.")


# --- Graph Extraction Prompt ---
GRAPH_EXTRACTION_PROMPT = """
Anda adalah ahli dalam Information Extraction. Dari teks di bawah ini, ekstrak semua entitas penting dan hubungan di antaranya.
Tugas Anda adalah mengidentifikasi Subjek, Label Subjek, Hubungan, Objek, dan Label Objek.
Label yang valid adalah: 'PERSON', 'ORGANIZATION', 'ROLE', 'PROJECT', 'LOCATION', 'DATE', 'DOCUMENT'.

Format output Anda HARUS berupa sebuah string JSON yang valid, berisi sebuah list dari list.
Setiap list di dalamnya harus memiliki 5 elemen: [subjek, label_subjek, hubungan, objek, label_objek].

Contoh:
Teks: "Dalam proyek Presensi Face Recognition, Kimi Dandy Yudanarko adalah seorang Peserta. Sertifikat ini ditandatangani oleh Ely Mulyadi, Manajer TEFA JTI Innovation di Jember pada 29 Juni 2025."
JSON Output:
[
    ["Kimi Dandy Yudanarko", "PERSON", "ADALAH_SEORANG", "Peserta", "ROLE"],
    ["Ely Mulyadi", "PERSON", "MEMILIKI_JABATAN", "Manajer TEFA JTI Innovation", "ROLE"],
    ["Sertifikat", "DOCUMENT", "DITANDATANGANI_OLEH", "Ely Mulyadi", "PERSON"],
    ["Sertifikat", "DITERBITKAN_DI", "Jember", "LOCATION"],
    ["Sertifikat", "DITERBITKAN_PADA", "29 Juni 2025", "DATE"]
]

PENTING: Pastikan untuk mengekstrak nama lengkap dan jabatan selengkap mungkin. Hanya gunakan label yang telah ditentukan.

Teks untuk dianalisis:
---
{text}
---

JSON Output:
"""

# --- Cypher Query Templates ---
NEO4J_MERGE_QUERY = (
    "MERGE (h:{head_label} {{name: $head, filename: $filename}}) "
    "MERGE (t:{tail_label} {{name: $tail, filename: $filename}}) "
    "MERGE (h)-[:`{relation}`]->(t)"
)


# --- LLM Model Name ---

# --- Vector Database Path ---
CHROMA_DB_PATH = "data/chroma_db"
CHROMA_COLLECTION_NAME = "cognigraph_rag"


LLM_MODEL_NAME = "gemini-1.5-flash"
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"

# --- Question Rephrasing Prompt ---
REPHRASE_QUESTION_PROMPT = """Based on the following conversation history, rephrase the "Follow Up Input" to be a standalone question that contains all the necessary context from the chat history.

Chat History:
{chat_history}

Follow Up Input: {query}

Standalone question:"""

# --- Cypher Generation Prompt ---
CYPHER_GENERATION_PROMPT = """Anda adalah ahli Cypher. Ubah pertanyaan berikut menjadi query Cypher untuk Neo4j.
Skema Graph: Node memiliki label spesifik seperti :PERSON, :ROLE, :ORGANIZATION, dll. dan properti 'name'.
Hanya kembalikan query-nya, tanpa penjelasan atau markdown.

PENTING: Jaga agar semua nama entitas dan istilah (seperti jabatan atau nama lokasi) di dalam query Cypher SAMA PERSIS dengan yang ada di pertanyaan pengguna. JANGAN menerjemahkannya ke bahasa lain.

Contoh:
Pertanyaan: siapa manajer tefa?
Query: MATCH (p:PERSON)-[]->(r:ROLE) WHERE r.name CONTAINS 'Manajer TEFA' RETURN p.name

Pertanyaan: di mana sertifikat diterbitkan?
Query: MATCH (d:DOCUMENT)-[:DITERBITKAN_DI]->(l:LOCATION) RETURN l.name

Pertanyaan: {query}
Query:
"""

# --- Final Answer Prompt ---
FINAL_ANSWER_PROMPT = """
Anda adalah asisten AI yang cerdas dan ahli. Berdasarkan informasi yang sangat relevan di bawah ini—yang mencakup teks asli dan fakta-fakta kunci yang diekstrak—jawablah pertanyaan pengguna secara akurat dan langsung dalam Bahasa Indonesia.

INFORMASI YANG DITEMUKAN (KONTEKS GABUNGAN):
---
{context}
---

PERTANYAAN PENGGUNA:
{rephrased_query}

JAWABAN ANDA:
"""
