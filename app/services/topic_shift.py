"""E12 - Topic Shift (Versión con keywords expandidas)"""

from __future__ import annotations
import re
from .module_result import ModuleResult

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

# Palabras clave por dominio (expandidas para capturar más variaciones)
DOMAIN_KEYWORDS = {
    "programming": [
        "python", "programar", "codigo", "code", "programming", "software", "api",
        "debug", "funcion", "variable", "algoritmo", "datos", "data", "framework",
        "biblioteca", "libreria", "library", "script", "html", "css", "javascript"
    ],
    "weather": [
        "lluvia", "llover", "rain", "raining", "clima", "weather", "temperatura", 
        "temperature", "tormenta", "storm", "viento", "wind", "nube", "cloud",
        "soleado", "sunny", "nieve", "snow", "calor", "heat", "frio", "cold",
        "humedo", "humid", "descender", "descenderá", "bruscamente"
    ],
    "sports": [
        "futbol", "soccer", "gol", "goal", "partido", "match", "baloncesto",
        "basketball", "tenis", "tennis", "jugador", "player", "equipo", "team",
        "liga", "league", "campeon", "champion"
    ],
    "food": [
        "comida", "food", "cocina", "cook", "receta", "recipe", "restaurante",
        "restaurant", "plato", "dish", "ingrediente", "ingredient", "sabor",
        "flavor", "bebida", "drink", "vino", "wine", "cerveza", "beer"
    ],
    "finance": [
        "precio", "price", "mercado", "market", "stock", "acciones", "dolar",
        "dollar", "euro", "inflacion", "inflation", "banco", "bank", "inversion",
        "investment", "crypto", "bitcoin", "economia", "economy"
    ],
    "health": [
        "salud", "health", "sintoma", "symptom", "medico", "doctor", "enfermedad",
        "disease", "dolor", "pain", "tratamiento", "treatment", "hospital",
        "medicina", "medicine", "virus", "vacuna", "vaccine"
    ]
}

TRANSITIONS = [
    "sin embargo", "por otro lado", "ademas", "además", "en cambio",
    "cambiando de tema", "ahora bien", "por cierto", "a proposito",
    "however", "on the other hand", "by the way", "also", "meanwhile"
]

def _get_domain(text: str) -> tuple:
    """Detecta dominio basado en keywords. Retorna (dominio, confianza)."""
    text_lower = text.lower()
    best_domain = None
    best_count = 0
    
    for domain, keywords in DOMAIN_KEYWORDS.items():
        count = 0
        for kw in keywords:
            if kw in text_lower:
                count += 1
        if count > best_count:
            best_count = count
            best_domain = domain
    
    # Confianza: 1-2 palabras = baja, 3+ = alta
    confidence = "baja" if best_count <= 2 else "alta" if best_count >= 3 else "media"
    
    return best_domain, best_count, confidence

def _has_transition(text: str) -> bool:
    """Verifica si hay palabra de transición."""
    text_lower = text.lower()
    for t in TRANSITIONS:
        if t in text_lower:
            return True
    return False

def _enough_content(text: str) -> bool:
    """Verifica si hay suficiente contenido."""
    words = re.findall(r'[a-záéíóúñü]+', text.lower())
    return len(words) >= 8

def detect(text: str, penalty: float = 0.6) -> ModuleResult:
    """Detecta cambio abrupto de tema usando detección de dominio."""
    
    # Dividir en oraciones (mínimo 15 caracteres)
    sentences = [s.strip() for s in SENTENCE_RE.split(text) if len(s.strip()) > 15]
    
    if len(sentences) < 3:
        return ModuleResult(
            code="E12", 
            name="Topic Shift", 
            triggered=False,
            reason="insufficient sentences (minimum 3)"
        )
    
    # Para textos cortos, threshold más alto
    is_short = len(sentences) <= 5
    
    # Detectar dominios por ventanas de contexto
    changes = []
    
    for i in range(1, len(sentences)):
        # Ventana izquierda: 2 oraciones anteriores
        left_start = max(0, i - 2)
        left_context = " ".join(sentences[left_start:i])
        
        # Ventana derecha: oración actual + 1 siguiente
        right_end = min(len(sentences), i + 2)
        right_context = " ".join(sentences[i:right_end])
        
        # Verificar contenido suficiente
        if not _enough_content(left_context) or not _enough_content(right_context):
            continue
        
        # Detectar dominios
        left_domain, left_count, left_conf = _get_domain(left_context)
        right_domain, right_count, right_conf = _get_domain(right_context)
        
        # Verificar transición
        has_trans = _has_transition(sentences[i])
        
        # Criterios para cambio abrupto:
        # 1. Ambos dominios detectados (no None)
        # 2. Dominios diferentes
        # 3. Suficientes palabras clave (al menos 2 en cada lado)
        # 4. Sin palabra de transición
        # 5. Para textos cortos, requerir mayor confianza
        
        if (left_domain is not None and 
            right_domain is not None and 
            left_domain != right_domain and
            left_count >= 2 and 
            right_count >= 2 and
            not has_trans):
            
            # Para textos cortos, requerir al menos una confianza "alta"
            if is_short and left_conf != "alta" and right_conf != "alta":
                continue
            
            changes.append({
                "position": i,
                "from_domain": left_domain,
                "to_domain": right_domain,
                "left_confidence": left_conf,
                "right_confidence": right_conf,
                "sentence": sentences[i][:80]
            })
    
    if changes:
        return ModuleResult(
            code="E12",
            name="Topic Shift",
            triggered=True,
            penalty=penalty,
            reason=f"abrupt topic shift from {changes[0]['from_domain']} to {changes[0]['to_domain']}",
            evidence={"shifts": changes[:3]}
        )
    
    return ModuleResult(
        code="E12", 
        name="Topic Shift", 
        triggered=False,
        reason="no significant topic shift detected"
    )

def run(text: str) -> ModuleResult:
    return detect(text)