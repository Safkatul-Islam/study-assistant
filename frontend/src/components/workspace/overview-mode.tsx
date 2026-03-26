"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ErrorMessage } from "@/components/ui/error-message";
import { Skeleton } from "@/components/ui/skeleton";
import { FlashcardStatsDisplay } from "@/components/workspace/flashcard-stats";
import { DifficultyFilter } from "@/components/workspace/difficulty-filter";
import { FlashcardGrid } from "@/components/workspace/flashcard-grid";
import { useFlashcards, useDeleteAllFlashcards } from "@/hooks/use-flashcards";
import { getApiErrorMessage } from "@/lib/utils";
import type { FlashcardStats } from "@/types/api";

interface OverviewModeProps {
  documentId: string;
  stats: FlashcardStats;
  onRegenerate: () => void;
}

export function OverviewMode({ documentId, stats, onRegenerate }: OverviewModeProps) {
  const [difficultyFilter, setDifficultyFilter] = useState("all");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const filterParam = difficultyFilter !== "all" ? difficultyFilter : undefined;
  const { data, isLoading, error } = useFlashcards(documentId, filterParam);
  const deleteAll = useDeleteAllFlashcards(documentId);

  const handleDeleteAll = () => {
    deleteAll.mutate(undefined, {
      onSuccess: () => {
        setShowDeleteConfirm(false);
        onRegenerate();
      },
    });
  };

  return (
    <div className="space-y-6">
      <FlashcardStatsDisplay stats={stats} />

      <div className="flex items-center justify-between gap-4 flex-wrap">
        <DifficultyFilter
          selected={difficultyFilter}
          onChange={setDifficultyFilter}
          stats={stats}
        />
        <Button
          variant="danger"
          size="sm"
          onClick={() => setShowDeleteConfirm(true)}
        >
          Regenerate
        </Button>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      )}

      {error && (
        <ErrorMessage
          message={getApiErrorMessage(error) || "Failed to load flashcards"}
        />
      )}

      {data?.flashcards && <FlashcardGrid flashcards={data.flashcards} />}

      {/* Delete confirmation overlay */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-sm w-full mx-4 space-y-4">
            <h4 className="text-base font-semibold text-gray-900">
              Delete all flashcards?
            </h4>
            <p className="text-sm text-gray-600">
              This will delete all existing flashcards and regenerate new ones. This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowDeleteConfirm(false)}
                disabled={deleteAll.isPending}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleDeleteAll}
                isLoading={deleteAll.isPending}
              >
                Confirm
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
