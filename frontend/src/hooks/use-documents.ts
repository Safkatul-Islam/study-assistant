"use client";

import { useQuery } from "@tanstack/react-query";
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
