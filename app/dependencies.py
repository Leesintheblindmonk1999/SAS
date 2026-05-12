"""
app/dependencies.py - SAS shared FastAPI dependencies.

Existing routers use get_api_key() as a dependency. The real authentication and
quota enforcement is handled by app.services.auth.api_key_auth_middleware.
This dependency remains as a compatibility guard and exposes the current user.
"""

from __future__ import annotations

from fastapi import Header, HTTPException, Request

from app.db.auth_store import init_auth_db
from app.services.auth import verify_api_key_value

# Initialize auth DB for compatibility with older imports.
init_auth_db()


async def get_api_key(
    request: Request,
    api_key: str = Header(..., alias="X-API-Key"),
):
    user = getattr(request.state, "api_user", None)
    if not user:
        try:
            user = verify_api_key_value(api_key)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or missing API Key")

    return {
        "user_id": user.get("id"),
        "plan": user.get("plan"),
        "email_hash": user.get("email_hash"),
    }
