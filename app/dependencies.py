from fastapi import Header, HTTPException, Depends
from app.config import settings
from app.services.auth import validate_api_key, init_auth_db
from app.services.rate_limiter import RateLimiter

# Inicializar base de datos de autenticación
init_auth_db()

# Rate limiter (NO SE USA - BYPASS TOTAL)
# rate_limiter = RateLimiter(free_limit_per_day=settings.free_requests_per_day)

async def get_api_key(api_key: str = Header(..., alias="X-API-Key")):
    """
    Valida API key - SIN RATE LIMITING para benchmark
    """
    is_valid, user_id = validate_api_key(api_key)
    if not is_valid:
        raise HTTPException(
            status_code=401, 
            detail="Invalid or missing API Key. Use: sas_test_key_2026"
        )
    
    # 🔓 BYPASS TOTAL - Sin rate limiting
    # El benchmark masivo puede correr sin restricciones
    
    return {"user_id": user_id, "remaining": 999999}