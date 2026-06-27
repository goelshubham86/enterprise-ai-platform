import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { chatApi } from '@/api/chat';
import type { ChatMessage } from '@/types';

function createUserMessage(content: string): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role: 'user',
    content,
    sources: [],
    createdAt: new Date().toISOString(),
    latencyMs: null,
    modelId: null,
  };
}

export function useChat(initialSessionId: string | null = null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(initialSessionId);

  const sendMutation = useMutation({
    mutationFn: chatApi.send,
    onSuccess: (response) => {
      setSessionId(response.sessionId);
      setMessages((prev) => [...prev, response.message]);
    },
  });

  const send = useCallback(
    (question: string) => {
      const userMsg = createUserMessage(question);
      setMessages((prev) => [...prev, userMsg]);

      sendMutation.mutate({
        sessionId,
        question,
        documentIds: [],
      });
    },
    [sessionId, sendMutation],
  );

  const clearSession = useCallback(() => {
    setMessages([]);
    setSessionId(null);
  }, []);

  return {
    messages,
    sessionId,
    isLoading: sendMutation.isPending,
    error: sendMutation.error,
    send,
    clearSession,
  };
}
