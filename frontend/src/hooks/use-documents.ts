"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Document } from "@/types/api";

interface DocumentListResponse {
  ok: boolean;
  documents: Document[];
}

export function useDocuments() {
  return useQuery({
    queryKey: ["documents"],
    queryFn: async () => {
      const { data } = await api.get<DocumentListResponse>("/documents");
      return data.documents;
    },
    refetchInterval: (query) => {
      const documents = query.state.data;
      if (!documents) return false;
      const hasProcessing = documents.some((d) => d.status === "processing");
      return hasProcessing ? 4000 : false;
    },
  });
}

export function useRenameDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ documentId, title }: { documentId: string; title: string }) => {
      const { data } = await api.patch(`/documents/${documentId}`, { title });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (documentId: string) => {
      await api.delete(`/documents/${documentId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useUpdateTags() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ documentId, tags }: { documentId: string; tags: string[] }) => {
      const { data } = await api.put(`/documents/${documentId}/tags`, { tags });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}
