"use client";

import { useState } from "react";

import { ErrorMessage } from "@/components/ui/error-message";
import { Skeleton } from "@/components/ui/skeleton";
import { GenerateFlashcards } from "@/components/workspace/generate-flashcards";
import { StudyMode } from "@/components/workspace/study-mode";
import { OverviewMode } from "@/components/workspace/overview-mode";
import { useStudyQueue } from "@/hooks/use-flashcards";
import { cn, getApiErrorMessage } from "@/lib/utils";

interface PracticePanelProps {
  documentId: string;
}

type Mode = "study" | "overview";

export function PracticePanel({ documentId }: PracticePanelProps) {
  const [mode, setMode] = useState<Mode>("study");
  const [showGenerate, setShowGenerate] = useState(false);

  const { data, isLoading, error } = useStudyQueue(documentId);

  if (isLoading) {
    return <PracticeSkeleton />;
  }

  if (error) {
    return <ErrorMessage message={getApiErrorMessage(error) || "Failed to load flashcards"} />;
  }

  if (!data || data.stats.total === 0 || showGenerate) {
    return <GenerateFlashcards documentId={documentId} />;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Mode toggle */}
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1 w-fit mb-4">
        {(["study", "overview"] as Mode[]).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={cn(
              "px-4 py-1.5 text-sm font-medium rounded-md transition-colors capitalize",
              mode === m
                ? "bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
            )}
          >
            {m}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0">
        {mode === "study" && (
          <StudyMode
            documentId={documentId}
            flashcards={data.flashcards}
            stats={data.stats}
          />
        )}
        {mode === "overview" && (
          <OverviewMode
            documentId={documentId}
            stats={data.stats}
            onRegenerate={() => setShowGenerate(true)}
          />
        )}
      </div>
    </div>
  );
}

function PracticeSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex gap-1">
        <Skeleton className="h-8 w-20 rounded-md" />
        <Skeleton className="h-8 w-24 rounded-md" />
      </div>
      <div className="flex gap-4">
        <Skeleton className="h-20 flex-1" />
        <Skeleton className="h-20 flex-1" />
        <Skeleton className="h-20 flex-1" />
        <Skeleton className="h-20 flex-1" />
      </div>
      <Skeleton className="h-64 w-full rounded-2xl" />
      <div className="flex gap-3 justify-center">
        <Skeleton className="h-10 w-20 rounded-lg" />
        <Skeleton className="h-10 w-24 rounded-lg" />
        <Skeleton className="h-10 w-20 rounded-lg" />
      </div>
    </div>
  );
}
