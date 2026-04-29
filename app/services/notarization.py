import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.merkle_tree import build_merkle_root

def generate_certificate(data: Dict[str, Any], fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Genera un certificado de integridad para un objeto JSON.
    - Construye una lista de hashes de los campos especificados (o de todo el objeto si no se especifican).
    - Calcula el Root Hash mediante Merkle tree.
    - Añade timestamp.
    """
    if fields is None:
        # Usar todos los campos del diccionario
        field_names = list(data.keys())
    else:
        field_names = fields

    # Calcular hash de cada campo
    field_hashes = []
    for field in field_names:
        value = data.get(field, "")
        # Convertir a string estable (JSON ordenado) para evitar diferencias por orden
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, sort_keys=True, separators=(',', ':'))
        else:
            value_str = str(value)
        field_hash = hashlib.sha256(value_str.encode()).hexdigest()
        field_hashes.append(field_hash)

    # Calcular Merkle root
    merkle_root = build_merkle_root(field_hashes)

    # Hash global del documento completo (para compatibilidad con versiones anteriores)
    full_content = json.dumps(data, sort_keys=True, separators=(',', ':'))
    full_hash = hashlib.sha256(full_content.encode()).hexdigest()

    return {
        "root_hash": full_hash,
        "merkle_root": merkle_root,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "fields": field_names,
        "field_hashes": field_hashes
    }

def verify_certificate(data: Dict[str, Any], certificate: Dict[str, Any]) -> bool:
    """
    Verifica que los datos actuales coincidan con el certificado.
    Recalcula el Merkle root y lo compara con el guardado.
    """
    recalc = generate_certificate(data, certificate.get("fields"))
    return recalc["merkle_root"] == certificate.get("merkle_root")