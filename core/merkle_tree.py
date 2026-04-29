import hashlib
from typing import List

def hash_pair(left: str, right: str) -> str:
    """Calcula el hash de dos hashes concatenados."""
    combined = left + right
    return hashlib.sha256(combined.encode()).hexdigest()

def build_merkle_root(hashes: List[str]) -> str:
    """
    Construye un árbol de Merkle y devuelve la raíz.
    Si la lista está vacía, devuelve cadena vacía.
    """
    if not hashes:
        return ""
    if len(hashes) == 1:
        return hashes[0]
    # Asegurar número par duplicando el último si es necesario
    if len(hashes) % 2 != 0:
        hashes.append(hashes[-1])

    new_level = []
    for i in range(0, len(hashes), 2):
        parent = hash_pair(hashes[i], hashes[i+1])
        new_level.append(parent)
    return build_merkle_root(new_level)