from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.notarization import generate_certificate, verify_certificate


router = APIRouter(prefix="/v1", tags=["notarization"])


class NotarizeRequest(BaseModel):
    data: Dict[str, Any]
    fields: Optional[List[str]] = None


class VerifyCertificateRequest(BaseModel):
    data: Dict[str, Any]
    certificate: Dict[str, Any]


@router.post("/notarize")
async def notarize_endpoint(request: NotarizeRequest) -> Dict[str, Any]:
    return generate_certificate(request.data, request.fields)


@router.post("/verify_certificate")
async def verify_certificate_endpoint(request: VerifyCertificateRequest) -> Dict[str, bool]:
    return {"valid": verify_certificate(request.data, request.certificate)}
