import os
import logging

# Uses the Docker compose service name mock-llm
LLM_URL = os.getenv("LLM_URL", "http://mock-llm:8001/v1/chat/completions")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "claude-opus-4-6")
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "Anthropic")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)