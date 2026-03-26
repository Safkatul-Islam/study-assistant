import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import api from "@/lib/api";
import type {
  FlashcardsResponse,
  FlashcardGenerateResponse,
  FlashcardResponse,
  StudyQueueResponse,
} from "@/types/api";

export function useFlashcards(documentId: string, difficulty?: string) {
  return useQuery({
    queryKey: ["flashcards", documentId, difficulty],
    queryFn: async () => {
      const params = difficulty ? { difficulty } : {};
      const { data } = await api.get<FlashcardsResponse>(
        `/documents/${documentId}/flashcards`,
        { params }
      );
      return data;
    },
    enabled: !!documentId,
  });
}

export function useStudyQueue(documentId: string) {
  return useQuery({
    queryKey: ["study-queue", documentId],
    queryFn: async () => {
      const { data } = await api.get<StudyQueueResponse>(
        `/documents/${documentId}/flashcards/study`
      );
      return data;
    },
    enabled: !!documentId,
  });
}

export function useGenerateFlashcards(documentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ regenerate }: { regenerate?: boolean } = {}) => {
      const { data } = await api.post<FlashcardGenerateResponse>(
        `/documents/${documentId}/flashcards`,
        { regenerate }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["flashcards", documentId],
      });
      queryClient.invalidateQueries({
        queryKey: ["study-queue", documentId],
      });
    },
  });
}

export function useUpdateFlashcard(documentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      flashcardId,
      ...body
    }: {
      flashcardId: string;
      difficulty?: string;
      front?: string;
      back?: string;
    }) => {
      const { data } = await api.patch<FlashcardResponse>(
        `/documents/${documentId}/flashcards/${flashcardId}`,
        body
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["flashcards", documentId],
      });
      queryClient.invalidateQueries({
        queryKey: ["study-queue", documentId],
      });
    },
  });
}

export function useDeleteFlashcard(documentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (flashcardId: string) => {
      await api.delete(`/documents/${documentId}/flashcards/${flashcardId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["flashcards", documentId],
      });
      queryClient.invalidateQueries({
        queryKey: ["study-queue", documentId],
      });
    },
  });
}

export function useDeleteAllFlashcards(documentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      await api.delete(`/documents/${documentId}/flashcards`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["flashcards", documentId],
      });
      queryClient.invalidateQueries({
        queryKey: ["study-queue", documentId],
      });
    },
  });
}
