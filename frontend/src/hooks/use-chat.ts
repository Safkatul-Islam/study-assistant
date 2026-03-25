import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import api from "@/lib/api";
import type {
  ChatHistoryResponse,
  ChatResponseData,
  ChatSessionsResponse,
} from "@/types/api";

export function useChatSessions(documentId: string) {
  return useQuery({
    queryKey: ["chat-sessions", documentId],
    queryFn: async () => {
      const { data } = await api.get<ChatSessionsResponse>(
        `/documents/${documentId}/chat`
      );
      return data.sessions;
    },
    enabled: !!documentId,
  });
}

export function useChatHistory(
  documentId: string,
  sessionId: string | null
) {
  return useQuery({
    queryKey: ["chat-history", documentId, sessionId],
    queryFn: async () => {
      const { data } = await api.get<ChatHistoryResponse>(
        `/documents/${documentId}/chat/${sessionId}`
      );
      return data;
    },
    enabled: !!documentId && !!sessionId,
  });
}

export function useSendMessage(documentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      message,
      sessionId,
    }: {
      message: string;
      sessionId: string | null;
    }) => {
      const { data } = await api.post<ChatResponseData>(
        `/documents/${documentId}/chat`,
        {
          message,
          session_id: sessionId,
        }
      );
      return data;
    },
    onSuccess: (data) => {
      // Invalidate session list and history to refetch
      queryClient.invalidateQueries({
        queryKey: ["chat-sessions", documentId],
      });
      if (data.session_id) {
        queryClient.invalidateQueries({
          queryKey: ["chat-history", documentId, data.session_id],
        });
      }
    },
  });
}
