import hashlib
import secrets
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent.parent / "auth.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_auth_db():
    """Inicializa la base de datos de autenticación - llamar al inicio"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key_hash TEXT UNIQUE NOT NULL,
                is_premium BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP
            )
        """)
        conn.commit()
        
        # Crear API key por defecto para pruebas (solo si la tabla está vacía)
        cursor = conn.execute("SELECT COUNT(*) as count FROM users")
        if cursor.fetchone()["count"] == 0:
            default_key = "sas_test_key_2026"
            key_hash = hashlib.sha256(default_key.encode()).hexdigest()
            conn.execute(
                "INSERT INTO users (api_key_hash, is_premium) VALUES (?, ?)",
                (key_hash, 1)
            )
            conn.commit()
            print(f"✅ Base de datos inicializada. API key por defecto: {default_key}")

def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def generate_api_key() -> str:
    return f"sas_{secrets.token_urlsafe(32)}"

def create_new_user(is_premium: bool = False) -> str:
    """Genera una nueva API key y la guarda en DB. Retorna la key en texto plano."""
    init_auth_db()
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)
    
    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (api_key_hash, is_premium) VALUES (?, ?)",
            (key_hash, 1 if is_premium else 0)
        )
        conn.commit()
    
    return raw_key

def validate_api_key(api_key: str) -> tuple[bool, int | None]:
    """Valida una API key. Retorna (es_válida, user_id)"""
    if not api_key or len(api_key) < 5:
        return False, None
    
    key_hash = hash_api_key(api_key)
    
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT id, is_premium FROM users WHERE api_key_hash = ?",
            (key_hash,)
        )
        user = cursor.fetchone()
        
        if user:
            # Actualizar last_used
            conn.execute(
                "UPDATE users SET last_used = CURRENT_TIMESTAMP WHERE id = ?",
                (user["id"],)
            )
            conn.commit()
            return True, user["id"]
    
    return False, None

def verify_api_key(api_key: str) -> bool:
    """Return True if the API key exists in the auth DB, False otherwise."""
    is_valid, _ = validate_api_key(api_key)
    return is_valid