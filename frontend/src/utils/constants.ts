export const QUERY_KEYS = {
  documents: ['documents'] as const,
  document: (id: string) => ['documents', id] as const,
  health: ['health'] as const,
  chatSessions: ['chat-sessions'] as const,
  chatSession: (id: string) => ['chat-sessions', id] as const,
} as const;

export const ROUTES = {
  dashboard: '/',
  chat: '/chat',
  documents: '/documents',
  settings: '/settings',
  health: '/health',
} as const;

export const MAX_UPLOAD_SIZE_MB = 50;
export const MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024;
export const ACCEPTED_MIME_TYPES = ['application/pdf', 'text/plain', 'text/markdown'];
export const SIDEBAR_WIDTH = 240;
export const NAVBAR_HEIGHT = 64;
