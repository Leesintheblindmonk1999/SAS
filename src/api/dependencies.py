from fastapi import Header, HTTPException, Depends
from app.config import settings
from app.services.auth import validate_api_key, init_auth_db
from app.services.rate_limiter import RateLimiter

# Inicializar base de datos de autenticación al cargar el módulo
init_auth_db()

# Rate limiter global
rate_limiter = RateLimiter(free_limit_per_day=settings.free_requests_per_day)

async def get_api_key(api_key: str = Header(..., alias="X-API-Key")):
    """
    Valida API key y aplica rate limiting.
    Requiere header X-API-Key en cada request.
    """
    is_valid, user_id = validate_api_key(api_key)
    if not is_valid:
        raise HTTPException(
            status_code=401, 
            detail="Invalid or missing API Key. Get a key at /admin/generate-key"
        )
    
    # Rate limiting
    can_request, remaining = await rate_limiter.can_make_request(
        api_key_hash=api_key,
        endpoint="audit"
    )
    if not can_request:
        raise HTTPException(
            status_code=429, 
            detail=f"Rate limit exceeded. Max {rate_limiter.free_limit} requests per day."
        )
    
    return {"user_id": user_id, "remaining": remaining}