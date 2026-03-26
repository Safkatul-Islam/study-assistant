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


# --- Flashcards ---

class FlashcardGenerateRequest(BaseModel):
    regenerate: bool = False


class FlashcardOut(BaseModel):
    id: str
    front: str
    back: str
    difficulty: str
    source_chunk_id: str | None
    last_reviewed_at: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class FlashcardGenerateResponse(BaseModel):
    ok: bool = True
    flashcards: list[FlashcardOut]
    generated_count: int
    was_cached: bool


class FlashcardListResponse(BaseModel):
    ok: bool = True
    flashcards: list[FlashcardOut]
    total: int
    offset: int
    limit: int


class FlashcardDetailResponse(BaseModel):
    ok: bool = True
    flashcard: FlashcardOut


class FlashcardUpdateRequest(BaseModel):
    front: str | None = Field(None, min_length=1, max_length=2000)
    back: str | None = Field(None, min_length=1, max_length=5000)
    difficulty: str | None = Field(None, pattern="^(unrated|easy|medium|hard)$")


class FlashcardStatsOut(BaseModel):
    total: int
    unrated: int
    easy: int
    medium: int
    hard: int


class StudyQueueResponse(BaseModel):
    ok: bool = True
    flashcards: list[FlashcardOut]
    stats: FlashcardStatsOut


class DeleteFlashcardsResponse(BaseModel):
    ok: bool = True
    deleted_count: int
