// ─── Document Domain ──────────────────────────────────────────

export type DocumentStatus = 'uploading' | 'processing' | 'indexed' | 'failed';

export interface Document {
  id: string;
  name: string;
  size: number;
  mimeType: string;
  status: DocumentStatus;
  chunkCount: number;
  uploadedAt: string;
  indexedAt: string | null;
  errorMessage: string | null;
}

export interface DocumentUploadResponse {
  id: string;
  name: string;
  status: DocumentStatus;
  message: string;
}

// ─── Chat Domain ──────────────────────────────────────────────

export type MessageRole = 'user' | 'assistant' | 'system';

export interface Source {
  documentId: string;
  documentName: string;
  chunkText: string;
  score: number;
  pageNumber: number | null;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  sources: Source[];
  createdAt: string;
  latencyMs: number | null;
  modelId: string | null;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  messageCount: number;
}

export interface ChatRequest {
  sessionId: string | null;
  question: string;
  documentIds: string[];
}

export interface ChatResponse {
  sessionId: string;
  message: ChatMessage;
}

// ─── Health Domain ────────────────────────────────────────────

export type ServiceStatus = 'healthy' | 'degraded' | 'unhealthy';

export interface ServiceHealth {
  name: string;
  status: ServiceStatus;
  latencyMs: number | null;
  details: string | null;
}

export interface HealthStatus {
  status: ServiceStatus;
  version: string;
  environment: string;
  uptime: number;
  services: ServiceHealth[];
  checkedAt: string;
}

// ─── API Primitives ───────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
}

export interface ApiError {
  detail: string;
  code: string;
  requestId: string;
}

// ─── UI State ─────────────────────────────────────────────────

export interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  badge?: number;
}
