"""
File ini mendefinisikan skema data Pydantic yang digunakan untuk validasi
permintaan (request) dan respons (response) di seluruh API FastAPI.

Memisahkan skema ke dalam file ini membantu menjaga kebersihan kode dan memisahkan
logika bisnis dari definisi struktur data.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict

class QueryRequest(BaseModel):
    """
    Skema untuk validasi data pada endpoint /query/.

    Attributes:
        query (str): Pertanyaan yang diajukan oleh pengguna.
        filenames (List[str]): Daftar nama file yang akan dijadikan sumber konteks.
        chat_history (Optional[List[Dict[str, str]]]): Riwayat percakapan sebelumnya
            untuk mendukung pertanyaan lanjutan. Format: `[{"role": "user/assistant", "content": "..."}]`
    """
    query: str
    filenames: List[str]
    chat_history: Optional[List[Dict[str, str]]] = None
