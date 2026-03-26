"use client";

import { Button } from "@/components/ui/button";
import { ErrorMessage } from "@/components/ui/error-message";
import { useGenerateFlashcards } from "@/hooks/use-flashcards";
import { getApiErrorMessage } from "@/lib/utils";

interface GenerateFlashcardsProps {
  documentId: string;
}

export function GenerateFlashcards({ documentId }: GenerateFlashcardsProps) {
  const generate = useGenerateFlashcards(documentId);

  return (
    <div className="flex flex-col items-center justify-center h-full gap-4">
      <svg
        width="48"
        height="48"
        viewBox="0 0 48 48"
        fill="none"
        className="text-gray-300"
      >
        <rect x="4" y="8" width="28" height="32" rx="3" stroke="currentColor" strokeWidth="2" />
        <rect x="16" y="8" width="28" height="32" rx="3" stroke="currentColor" strokeWidth="2" />
        <circle cx="30" cy="24" r="4" stroke="currentColor" strokeWidth="2" />
        <path d="M30 20v-2M30 30v-2M34 24h2M26 24h-2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>

      <h3 className="text-lg font-semibold text-gray-900">
        Generate Flashcards
      </h3>
      <p className="text-sm text-gray-500 text-center max-w-xs">
        AI will create study flashcards from your document
      </p>

      <Button
        onClick={() => generate.mutate({})}
        isLoading={generate.isPending}
        size="md"
      >
        Generate
      </Button>

      {generate.isError && (
        <ErrorMessage
          message={getApiErrorMessage(generate.error) || "Failed to generate flashcards"}
        />
      )}
    </div>
  );
}
