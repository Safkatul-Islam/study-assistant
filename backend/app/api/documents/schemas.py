from datetime import datetime

from pydantic import BaseModel, Field


class InitUploadRequest(BaseModel):
    file_name: str
    file_size: int
    content_type: str = "application/pdf"


class InitUploadResponse(BaseModel):
    ok: bool = True
    document_id: str
    upload_url: str
    s3_key: str


class CompleteUploadRequest(BaseModel):
    document_id: str


class DocumentOut(BaseModel):
    id: str
    title: str
    file_name: str
    file_size: int
    page_count: int | None
    status: str
    error_message: str | None
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    ok: bool = True
    document: DocumentOut


class DocumentListResponse(BaseModel):
    ok: bool = True
    documents: list[DocumentOut]


class RenameDocumentRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)


class UpdateTagsRequest(BaseModel):
    tags: list[str] = Field(default_factory=list, max_length=20)
