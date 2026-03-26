"use client";

import { cn } from "@/lib/utils";
import type { Flashcard } from "@/types/api";

interface FlashcardGridProps {
  flashcards: Flashcard[];
}

const difficultyStyles: Record<string, string> = {
  unrated: "bg-gray-100 text-gray-600",
  easy: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-800",
  hard: "bg-red-100 text-red-700",
};

export function FlashcardGrid({ flashcards }: FlashcardGridProps) {
  if (flashcards.length === 0) {
    return (
      <p className="text-sm text-gray-400 text-center py-8">
        No flashcards match this filter.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {flashcards.map((card) => (
        <div
          key={card.id}
          className="bg-white rounded-xl shadow-sm border p-4 relative"
        >
          <span
            className={cn(
              "absolute top-3 right-3 rounded-full px-2 py-0.5 text-xs font-medium",
              difficultyStyles[card.difficulty]
            )}
          >
            {card.difficulty}
          </span>
          <p className="text-sm text-gray-900 line-clamp-2 pr-16">
            {card.front}
          </p>
          <p className="text-xs text-gray-500 mt-2 line-clamp-1">
            {card.back}
          </p>
        </div>
      ))}
    </div>
  );
}
