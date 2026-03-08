from fastapi import APIRouter

from app.api.auth.router import router as auth_router
from app.api.documents.router import router as documents_router
from app.api.workspace.router import router as workspace_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(workspace_router, prefix="/documents", tags=["workspace"])
