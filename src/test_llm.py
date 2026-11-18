"""Testa a ligação ao Gemini e lista os modelos disponíveis."""
import os

import requests
from common import get_llm

# 1) Lista os modelos que a chave pode usar
r = requests.get(
    "https://generativelanguage.googleapis.com/v1beta/models",
    params={"key": os.getenv("GOOGLE_API_KEY"), "pageSize": 100},
    timeout=30,
)
r.raise_for_status()
print("Modelos com generateContent:")
for m in r.json().get("models", []):
    if "generateContent" in m.get("supportedGenerationMethods", []):
        print("  ", m["name"].replace("models/", ""))

# 2) Testa uma chamada ao modelo configurado
llm = get_llm()
print("\nResposta do modelo:")
print(llm.invoke("Responde apenas com a palavra: OK").content)