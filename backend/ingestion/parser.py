from unstructured.partition.auto import partition
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def parse_document(file_path: str) -> str:
    """
    Mengekstrak konten teks mentah dari sebuah file dokumen secara komprehensif.

    Fungsi ini adalah titik awal dari pipeline ingesti. Ia menggunakan pustaka `unstructured`
    dengan strategi 'hi_res'. Strategi ini dipilih karena kemampuannya menangani dokumen
    kompleks (seperti PDF) yang mungkin berisi teks, tabel, dan gambar. 'hi_res' secara
    otomatis akan menerapkan OCR (Optical Character Recognition) jika diperlukan.

    Args:
        file_path (str): Path absolut menuju file yang akan diproses.

    Returns:
        str: Konten teks yang telah diekstrak. Mengembalikan string kosong jika terjadi kegagalan.
    """
    filename = Path(file_path).name
    logger.info(f"Memulai proses parsing untuk dokumen: '{filename}'...")
    try:
        # `partition` adalah fungsi utama dari `unstructured` yang secara cerdas memilih
        # parser yang tepat berdasarkan tipe file. Bahasa 'ind' dan 'eng' 
        elements = partition(filename=file_path, strategy="hi_res", languages=["ind", "eng"])
        extracted_text = "\n\n".join([el.text for el in elements])
        
        logger.info(f"Berhasil mem-parsing dokumen '{filename}'. Total karakter diekstrak: {len(extracted_text)}")
        return extracted_text
    except Exception as e:
        logger.error(f"Terjadi kegagalan saat mem-parsing dokumen '{filename}': {e}", exc_info=True)
        return ""
