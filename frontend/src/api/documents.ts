import type { Document, DocumentUploadResponse, PaginatedResponse } from '@/types';
import { apiClient } from './client';

export const documentsApi = {
  list: async (page = 1, pageSize = 20): Promise<PaginatedResponse<Document>> => {
    const { data } = await apiClient.get<PaginatedResponse<Document>>('/documents', {
      params: { page, page_size: pageSize },
    });
    return data;
  },

  get: async (id: string): Promise<Document> => {
    const { data } = await apiClient.get<Document>(`/documents/${id}`);
    return data;
  },

  upload: async (file: File, onProgress?: (pct: number) => void): Promise<DocumentUploadResponse> => {
    const form = new FormData();
    form.append('file', file);
    const { data } = await apiClient.post<DocumentUploadResponse>('/documents/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (evt) => {
        if (evt.total && onProgress) {
          onProgress(Math.round((evt.loaded / evt.total) * 100));
        }
      },
    });
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/documents/${id}`);
  },

  reindex: async (id: string): Promise<void> => {
    await apiClient.post(`/documents/${id}/reindex`);
  },
};
