import { useQuery } from "@tanstack/react-query";

import api from "@/lib/api";
import type { SummaryResponse } from "@/types/api";

export function useSummary(documentId: string) {
  return useQuery({
    queryKey: ["summary", documentId],
    queryFn: async () => {
      const { data } = await api.get<SummaryResponse>(
        `/documents/${documentId}/summary`
      );
      return data;
    },
    enabled: !!documentId,
    staleTime: Infinity, // summaries are cached server-side
    retry: 1,
  });
}
