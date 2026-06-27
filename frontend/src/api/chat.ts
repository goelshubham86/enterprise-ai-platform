import type { ChatRequest, ChatResponse, ChatSession } from '@/types';
import { apiClient } from './client';

export const chatApi = {
  send: async (request: ChatRequest): Promise<ChatResponse> => {
    const { data } = await apiClient.post<ChatResponse>('/chat', request);
    return data;
  },

  getSessions: async (): Promise<ChatSession[]> => {
    const { data } = await apiClient.get<ChatSession[]>('/chat/sessions');
    return data;
  },

  getSession: async (sessionId: string): Promise<ChatSession> => {
    const { data } = await apiClient.get<ChatSession>(`/chat/sessions/${sessionId}`);
    return data;
  },

  deleteSession: async (sessionId: string): Promise<void> => {
    await apiClient.delete(`/chat/sessions/${sessionId}`);
  },
};
