import sqlite3
from datetime import datetime, date
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent.parent / "rate_limit.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_rate_db():
    """Ejecutar UNA vez al iniciar la API"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rate_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key_hash TEXT NOT NULL,
                request_date TEXT NOT NULL,
                endpoint TEXT NOT NULL
            )
        """)
        conn.commit()

class RateLimiter:
    def __init__(self, free_limit_per_day: int = 10000):
        self.free_limit = free_limit_per_day
        init_rate_db()
    
    async def can_make_request(self, api_key_hash: str, endpoint: str = "audit") -> tuple[bool, int]:
        today = date.today().isoformat()
        
        with get_db() as conn:
            # Contar requests hoy
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM rate_requests WHERE api_key_hash = ? AND request_date = ?",
                (api_key_hash, today)
            )
            row = cursor.fetchone()
            count = row["count"] if row else 0
            
            if count >= self.free_limit:
                return False, self.free_limit - count
            
            # Registrar este request
            conn.execute(
                "INSERT INTO rate_requests (api_key_hash, request_date, endpoint) VALUES (?, ?, ?)",
                (api_key_hash, today, endpoint)
            )
            conn.commit()
            
            remaining = self.free_limit - (count + 1)
            return True, remaining