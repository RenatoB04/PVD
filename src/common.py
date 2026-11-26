"""Utilitários partilhados: caminhos e LLM."""
import os
import warnings
warnings.filterwarnings("ignore", message=".*fixed sampling defaults.*")

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

# --- Dataset limpo (Etapa 1) ---
CONCELHO_CSV = "data/clean/consumos_concelho.csv"   # relativo à raiz do projeto
CONCELHO_DESC = """Ficheiro CSV (separador vírgula), um registo por concelho, mês e nível de tensão.
Colunas:
- data: data do mês (primeiro dia), ex. 2023-05-01; período 2020-11 a 2026-07 (69 meses)
- distrito (str): 18 distritos de Portugal continental
- cod_distrito (str): código com zero à esquerda, ex. '01'
- concelho (str): 278 concelhos
- cod_concelho (str): código com zero à esquerda, ex. '0102'
- nivel_tensao (str): 'BT' (baixa tensão) ou 'MT/AT/MAT' (média, alta e muito alta tensões)
- consumo_kwh (float): energia ativa faturada em kWh (sem nulos nem negativos)
Notas: alguns concelhos/meses não têm registo num dos níveis de tensão (tratar como 0 ao fazer pivot).
Ler com: pd.read_csv(DATA_PATH, dtype={'cod_distrito': str, 'cod_concelho': str}, parse_dates=['data'])"""


def content_to_text(content) -> str:
    """O Gemini pode devolver str ou lista de blocos; normaliza para texto."""
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts)