from unstructured.partition.auto import partition
import logging
from pathlib import Path

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def parse_document(file_path: str) -> str:
    """
    Mengekstrak konten teks dari sebuah dokumen secara asinkron.

    Fungsi ini menggunakan pustaka `unstructured` dengan strategi 'hi_res'
    untuk secara otomatis menangani berbagai format file dan menjalankan OCR
    pada gambar yang terdeteksi di dalam dokumen.

    Args:
        file_path (str): Path menuju file dokumen yang akan diparsing.

    Returns:
        str: Konten teks yang diekstrak dari dokumen. Mengembalikan string kosong
             jika terjadi kegagalan.
    """
    logger.info(f"Starting parsing for document: {file_path}")
    try:
        elements = partition(filename=file_path, strategy="hi_res", languages=["ind", "eng"])
        extracted_text = "\n\n".join([el.text for el in elements])
        logger.info(f"Berhasil mem-parsing dokumen {Path(file_path).name}. Total karakter: {len(extracted_text)}")
        return extracted_text
    except Exception as e:
        logger.error(f"Gagal mem-parsing dokumen {file_path}: {e}", exc_info=True)
        return ""
