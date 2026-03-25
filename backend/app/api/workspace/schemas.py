from pydantic import BaseModel, Field


# --- Summary ---

class SummaryOut(BaseModel):
    executive_summary: list[str]
    key_concepts: list[str]
    definitions: dict[str, str]
    possible_questions: list[str]


class SummaryResponse(BaseModel):
    ok: bool = True
    summary: SummaryOut
    cached: bool


# --- Chat ---

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: str | None = None


class CitationOut(BaseModel):
    chunk_id: str
    page_start: int | None
    page_end: int | None
    snippet: str


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    citations: list[CitationOut] | None = None
    created_at: str

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    ok: bool = True
    session_id: str
    message: ChatMessageOut


class ChatSessionOut(BaseModel):
    id: str
    title: str
    created_at: str

    model_config = {"from_attributes": True}


class ChatSessionsResponse(BaseModel):
    ok: bool = True
    sessions: list[ChatSessionOut]


class ChatHistoryResponse(BaseModel):
    ok: bool = True
    session: ChatSessionOut
    messages: list[ChatMessageOut]
