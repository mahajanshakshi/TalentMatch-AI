"""Application configuration and environment settings."""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"


def load_environment() -> None:
    """Load or reload environment variables from .env file."""
    if ENV_FILE.exists():
        load_dotenv(dotenv_path=ENV_FILE, override=True)
    else:
        load_dotenv(override=True)


# Initial load
load_environment()

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
)
logger = logging.getLogger("TalentMatchAI")

# App Metadata
APP_NAME = "TalentMatch AI"
APP_SUBTITLE = "Enterprise AI Resume Parser & Intelligent Job Matcher"
APP_VERSION = "1.0.0"

# Groq Settings
GROQ_TEMPERATURE = 0.0

# Supported file extensions
SUPPORTED_EXTENSIONS = [".pdf", ".docx"]

# Scoring weights (must sum to 1.0)
SCORING_WEIGHTS = {
    "skills_alignment": 0.40,
    "experience_relevance": 0.25,
    "responsibilities_fit": 0.20,
    "education_credentials": 0.15,
}

# Token budget constants
MAX_INPUT_TOKENS = 12000
MAX_OUTPUT_TOKENS = 4096


def get_effective_groq_api_key(override_key: str | None = None) -> str:
    """Return runtime override key if provided, else reload from .env."""
    if override_key and override_key.strip():
        return override_key.strip()
    load_environment()
    return os.getenv("GROQ_API_KEY", "").strip()


def get_configured_groq_model(override_model: str | None = None) -> str:
    """Return configured Groq model, refreshing from environment."""
    if override_model and override_model.strip():
        return override_model.strip()
    load_environment()
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()


def is_groq_configured(api_key: str | None = None) -> bool:
    """Check if a valid non-empty Groq API key is present."""
    key = get_effective_groq_api_key(api_key)
    return bool(key and len(key) > 10 and not key.startswith("your_"))


# Backward-compatible property access
GROQ_API_KEY = get_effective_groq_api_key()
GROQ_MODEL = get_configured_groq_model()
