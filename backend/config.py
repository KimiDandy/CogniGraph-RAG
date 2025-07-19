import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Google Gemini API Key ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY not found in environment variables. Please create a .env file and set it.")
    # raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
else:
    # Configure the generative AI model
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("Google Generative AI configured successfully.")


# --- LLM Model Name ---
# Using a fast and capable model. You can switch to 'gemini-pro' if needed.
LLM_MODEL_NAME = "gemini-1.5-flash-latest"
