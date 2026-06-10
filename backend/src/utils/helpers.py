import logging
import re
from httpx import Client
from langchain_openai import ChatOpenAI

from backend.src.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def get_llm(temperature: float = 0.1) -> ChatOpenAI:
    return ChatOpenAI(model=settings.llm_model, openai_api_key=settings.openai_api_key, openai_api_base=settings.openai_api_base, temperature=temperature, http_client=Client(proxy=None))


def get_device() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def normalize_whitespace(text: str) -> str:
    return "\n\n".join(re.sub(r"\s+", " ", p).strip() for p in text.split("\n\n"))
