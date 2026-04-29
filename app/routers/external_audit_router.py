from fastapi import APIRouter, Header, HTTPException
from app.services.external_audit import audit_external_model
from app.services.auth import verify_api_key
from app.models.request import ExternalAuditRequest
from app.models.response import ExternalAuditResponse

router = APIRouter(prefix="/v1", tags=["external_audit"])

@router.post("/audit_external_model", response_model=ExternalAuditResponse)
async def external_audit_endpoint(
    request: ExternalAuditRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    if not verify_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

    try:
        result = audit_external_model(request.model_name, request.api_key, request.prompt)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
