"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";

interface DownloadUrlResponse {
  ok: boolean;
  url: string;
}

export function usePdfUrl(documentId: string) {
  return useQuery({
    queryKey: ["pdf-url", documentId],
    queryFn: async () => {
      const { data } = await api.get<DownloadUrlResponse>(
        `/documents/${documentId}/download-url`
      );
      return data.url;
    },
    enabled: !!documentId,
    staleTime: 30 * 60 * 1000, // 30 min (URL expires in 1 hour)
  });
}
