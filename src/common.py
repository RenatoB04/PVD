"""Utilitários partilhados: caminhos e LLM."""
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_CLEAN = ROOT / "data" / "clean"
FIGURES = ROOT / "figures"

load_dotenv(ROOT / ".env")


def get_llm(temperature: float = 0.0):
    """Devolve o modelo Gemini configurado no .env."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY não definida no ficheiro .env")
    return ChatGoogleGenerativeAI(
        model=os.getenv("LLM_MODEL", "gemini-2.5-flash"),
        google_api_key=api_key,
        temperature=temperature,
    )