import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
# SECTION 1: KREDENSIAL & KONFIGURASI EKSTERNAL
# ==============================================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY tidak ditemukan di environment. Pastikan file .env sudah ada dan terisi.")

# Pengguna Windows mungkin perlu memverifikasi path ini sesuai dengan instalasi lokal.
# Untuk pengguna Linux/macOS, seringkali tidak perlu diatur jika sudah ada di PATH sistem.
TESSERACT_PATH = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

# --- Kredensial Database Neo4j ---
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
    logger.warning("Kredensial Neo4j tidak lengkap. Pastikan file .env sudah dikonfigurasi.")

# ==============================================================================
# SECTION 2: KONFIGURASI PENYIMPANAN & MODEL
# ==============================================================================

# --- Konfigurasi Vector Store (ChromaDB) ---
CHROMA_DB_PATH = "data/chroma_db"
CHROMA_COLLECTION_NAME = "cognigraph_rag"

# --- Konfigurasi Model AI ---
# Nama model yang digunakan untuk tugas LLM dan embedding.
LLM_MODEL_NAME = "gemini-2.5-flash"
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"

# ==============================================================================
# SECTION 3: TEMPLATE PROMPT UNTUK LLM
# ==============================================================================

# --- 1. Prompt Ekstraksi Knowledge Graph ---
# Prompt ini menginstruksikan LLM untuk bertindak sebagai ahli Information Extraction.
# Tujuannya adalah mengubah teks tidak terstruktur menjadi data terstruktur (triplets)
# yang akan menjadi fondasi knowledge graph. Aturan yang ketat (label, format JSON)
# diberikan untuk memastikan output yang konsisten dan mudah diproses.
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

# --- 2. Prompt Formulasi Ulang Pertanyaan (Rephrasing) ---
# Dalam mode percakapan, pengguna sering mengajukan pertanyaan lanjutan (e.g., "siapa dia?").
# Prompt ini bertugas mengubah pertanyaan lanjutan tersebut menjadi pertanyaan mandiri dengan menyertakan konteks dari riwayat percakapan, agar dapat dipahami oleh sistem RAG.
REPHRASE_QUESTION_PROMPT = """Based on the following conversation history, rephrase the "Follow Up Input" to be a standalone question that contains all the necessary context from the chat history.

Chat History:
{chat_history}

Follow Up Input: {query}

Standalone question:"""

# --- 3. Prompt Pembangkitan Kueri Cypher ---
# Prompt ini mengubah pertanyaan dalam bahasa alami menjadi kueri Cypher yang sintaktis.
# Ini adalah jembatan antara pertanyaan pengguna dan knowledge graph. Instruksi untuk tidak
# menerjemahkan entitas penting untuk memastikan kueri cocok dengan data di Neo4j.
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

# --- 4. Prompt Jawaban Akhir ---
# Prompt ini memberikan semua konteks yang telah dikumpulkan (dari vector search dan graph search) kepada LLM dan memintanya untuk
# menyusun jawaban akhir yang koheren, akurat, dan langsung dalam Bahasa Indonesia.
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

# ==============================================================================
# SECTION 4: TEMPLATE KUERI DATABASE
# ==============================================================================

# --- Kueri MERGE untuk Neo4j ---
# Kueri ini digunakan untuk menyimpan triplet ke Neo4j.
# `MERGE` akan membuat node atau relasi hanya jika belum ada, mencegah duplikasi
# data jika dokumen yang sama diproses ulang. Properti `filename` memastikan data dari dokumen yang berbeda tetap terisolasi.
NEO4J_MERGE_QUERY = (
    "MERGE (h:{head_label} {{name: $head, filename: $filename}}) "
    "MERGE (t:{tail_label} {{name: $tail, filename: $filename}}) "
    "MERGE (h)-[:`{relation}`]->(t)"
)
