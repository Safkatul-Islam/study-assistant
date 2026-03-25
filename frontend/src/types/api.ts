// Auth
export interface User {
  id: string;
  email: string;
  full_name: string;
}

export interface AuthResponse {
  ok: boolean;
  access_token: string;
  refresh_token: string;
  user: User;
}

// Documents
export interface Document {
  id: string;
  title: string;
  file_name: string;
  file_size: number;
  page_count: number | null;
  status: "uploaded" | "processing" | "ready" | "failed";
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface InitUploadResponse {
  ok: boolean;
  document_id: string;
  upload_url: string;
  s3_key: string;
}

// Workspace
export interface Summary {
  executive_summary: string[];
  key_concepts: string[];
  definitions: Record<string, string>;
  possible_questions: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[] | null;
}

export interface Citation {
  chunk_id: string;
  page_start: number | null;
  page_end: number | null;
  snippet: string;
}

export interface Flashcard {
  id: string;
  front: string;
  back: string;
  difficulty: "unrated" | "easy" | "medium" | "hard";
}

// Workspace responses
export interface SummaryResponse {
  ok: boolean;
  summary: Summary;
  cached: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
}

export interface ChatResponseData {
  ok: boolean;
  session_id: string;
  message: ChatMessage;
}

export interface ChatSessionsResponse {
  ok: boolean;
  sessions: ChatSession[];
}

export interface ChatHistoryResponse {
  ok: boolean;
  session: ChatSession;
  messages: ChatMessage[];
}

// Generic error envelope
export interface ApiError {
  ok: false;
  error: {
    message: string;
    details?: unknown;
  };
}
