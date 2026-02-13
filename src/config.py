import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Config:
    """Central configuration for TNEA AI."""
    
    try:
        import streamlit as st
        # Helper to get secrets from potentially nested TOML
        def _get_secret(key, section=None):
            if section and section in st.secrets and key in st.secrets[section]:
                return st.secrets[section][key]
            if key in st.secrets:
                return st.secrets[key]
            return None

        # Load critical secrets into environment variables
        api_key = _get_secret("NVIDIA_API_KEY", "nvidia")
        if api_key: os.environ["NVIDIA_API_KEY"] = api_key
        
        api_base = _get_secret("NVIDIA_API_BASE", "nvidia")
        if api_base: os.environ["NVIDIA_API_BASE"] = api_base
        
        model_name = _get_secret("MODEL_NAME", "nvidia")
        if model_name: os.environ["MODEL_NAME"] = model_name

        debug_val = _get_secret("DEBUG", "app")
        if debug_val is not None: os.environ["DEBUG"] = str(debug_val)

    except ImportError:
        pass
    except FileNotFoundError:
        pass # Secrets not found

    # API Configuration
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
    NVIDIA_API_BASE = os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")
    MODEL_NAME = os.getenv("MODEL_NAME", "qwen/qwen3-coder-480b-a35b-instruct")
    
    # App Settings
    APP_NAME = os.getenv("APP_NAME", "TNEA AI")
    VERSION = os.getenv("VERSION", "4.0.0")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    SRC_DIR = BASE_DIR / "src"
    DATA_DIR = BASE_DIR / "data"
    CONVERSATIONS_DIR = SRC_DIR / "conversations"
    
    # Ensure directories exist
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls):
        """Validate critical configuration."""
        if not cls.NVIDIA_API_KEY:
            raise ValueError("Missing NVIDIA_API_KEY. Please set it in .env file.")
        
config = Config()

# --- Logging Setup ---
_log_handlers = [logging.StreamHandler()]
try:
    _log_handlers.append(logging.FileHandler(config.BASE_DIR / 'tnea_ai.log', mode='a'))
except Exception:
    pass

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=_log_handlers,
)

logger = logging.getLogger("tnea_ai")
