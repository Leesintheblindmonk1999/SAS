import requests
from typing import Dict, Any
import time
import math
from core.semantic_diff import quick_diff  # Ajusta según tu función real de ISI

# Configuración de modelos externos (puedes ponerlo en config/env)
ENDPOINTS = {
    "claude-3.5-sonnet": "https://api.anthropic.com/v1/messages",
    "gemini-pro-1.5": "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
}

def _call_claude(api_key: str, prompt: str) -> str:
    # Implementar según la API de Anthropic
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    payload = {"model": "claude-3-5-sonnet-20241022", "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]}
    response = requests.post(ENDPOINTS["claude-3.5-sonnet"], headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["content"][0]["text"]

def _call_gemini(api_key: str, prompt: str) -> str:
    # Implementar según la API de Google
    url = f"{ENDPOINTS['gemini-pro-1.5']}?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]

def audit_external_model(model_name: str, api_key: str, prompt: str) -> Dict[str, Any]:
    """
    Audita un modelo externo llamándolo con un prompt conocido.
    Mide la ISI estructural entre prompt y respuesta.
    This is structural comparison, not plagiarism detection.
    """
    # 1. Obtener respuesta del modelo externo
    try:
        if "claude" in model_name.lower():
            response_text = _call_claude(api_key, prompt)
        elif "gemini" in model_name.lower():
            response_text = _call_gemini(api_key, prompt)
        else:
            raise ValueError(f"Modelo '{model_name}' no soportado")
    except Exception as e:
        raise RuntimeError(f"Error al llamar a {model_name}: {str(e)}")

    # 2. Calcular ISI (coherencia estructural)
    report = quick_diff(prompt, response_text)
    isi = report.invariant_similarity_index

    # 3. Calcular sigma (desviación respecto al umbral esperado)
    #    Fórmula simplificada: sigma = (isi - 0.5) / 0.05  (asumiendo desviación estándar 0.05)
    #    Puedes ajustarla según tus métricas de validación.
    expected = 0.5  # valor esperado para un modelo que no usa κD
    std = 0.05
    sigma = (isi - expected) / std

    # 4. Determinar riesgo de similitud estructural
    if sigma > 12.0:
        risk = "CRITICO"
    elif sigma > 7.0:
        risk = "ALTO"
    elif sigma > 3.0:
        risk = "MEDIO"
    else:
        risk = "BAJO"

    return {
        "model": model_name,
        "isi": round(isi, 4),
        "sigma": round(sigma, 2),
        "structural_similarity_risk": risk,
        "disclaimer": "This is structural comparison, not plagiarism detection",
        "response_preview": response_text[:200] + ("..." if len(response_text) > 200 else "")
    }