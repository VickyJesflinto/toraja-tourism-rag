"""
config/settings.py
Centralized configuration for Toraja Tourism RAG System
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Database ─────────────────────────────────────────────────────────────────
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", 3306))
DB_NAME     = os.getenv("DB_NAME", "toraja_tourism")
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?charset=utf8mb4"
)

# ─── LLM via OpenRouter ───────────────────────────────────────────────────────
# Dokumentasi: https://openrouter.ai/docs
# Daftar model: https://openrouter.ai/models
OPENROUTER_API_KEY   = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL  = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
# Format model ID OpenRouter: "<provider>/<model-name>"
# Contoh: "openai/gpt-4o", "meta-llama/llama-3.1-405b", "openai/gpt-oss-120b:free"
LLM_MODEL            = os.getenv("LLM_MODEL", "openai/gpt-oss-120b:free")
LLM_MAX_TOKENS       = int(os.getenv("LLM_MAX_TOKENS", 2048))
LLM_TEMPERATURE      = float(os.getenv("LLM_TEMPERATURE", 0.7))
# Dikirim ke OpenRouter untuk identifikasi app di dashboard usage mereka (opsional)
OPENROUTER_SITE_URL  = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8501")
OPENROUTER_APP_NAME  = os.getenv("OPENROUTER_APP_NAME", "Toraja Tourism RAG")

# ─── Embeddings ───────────────────────────────────────────────────────────────
EMBEDDING_MODEL     = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", 384))

# ─── FAISS ────────────────────────────────────────────────────────────────────
FAISS_INDEX_PATH = BASE_DIR / os.getenv("FAISS_INDEX_PATH", "data/faiss_index")
FAISS_K          = int(os.getenv("FAISS_K", 5))

# ─── RAGAS Evaluation — Judge LLM ──────────────────────────────────────────────
RAGAS_JUDGE_MODEL       = os.getenv("RAGAS_JUDGE_MODEL", "google/gemma-3-27b-it")
RAGAS_JUDGE_TEMPERATURE = float(os.getenv("RAGAS_JUDGE_TEMPERATURE", "0.0"))
RAGAS_JUDGE_MAX_TOKENS  = int(os.getenv("RAGAS_JUDGE_MAX_TOKENS", "800"))
RAGAS_N_QUESTIONS       = int(os.getenv("RAGAS_N_QUESTIONS", "3"))

# ─── App ──────────────────────────────────────────────────────────────────────
APP_SECRET_KEY  = os.getenv("APP_SECRET_KEY", "toraja-secret-2024")
ADMIN_USERNAME  = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD  = os.getenv("ADMIN_PASSWORD", "admin123")
APP_DEBUG       = os.getenv("APP_DEBUG", "False").lower() == "true"

# ─── Upload ───────────────────────────────────────────────────────────────────
UPLOAD_DIR       = BASE_DIR / "data" / "uploads"
ALLOWED_EXTENSIONS = {
    ".pdf", ".csv", ".json", ".txt", ".docx",
    ".xlsx", ".xls", ".pptx", ".html", ".xml"
}
MAX_UPLOAD_MB = 50

# ─── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR  = BASE_DIR / "data"
LOGS_DIR  = BASE_DIR / "logs"

# Ensure directories exist
for _dir in [UPLOAD_DIR, FAISS_INDEX_PATH, DATA_DIR, LOGS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# ─── MMR ────────────────────────────────────────────────────────────────────
MMR_ENABLED=True    # aktif/matikan
MMR_LAMBDA=0.5      # 0.0–1.0
MMR_FETCH_K=20      # ukuran candidate pool