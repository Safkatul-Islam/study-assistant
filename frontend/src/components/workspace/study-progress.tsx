"use client";

import type { FlashcardStats } from "@/types/api";

interface StudyProgressProps {
  current: number;
  total: number;
  stats: FlashcardStats;
}

export function StudyProgress({ current, total, stats }: StudyProgressProps) {
  const rated = stats.easy + stats.medium + stats.hard;
  const progressPercent = total > 0 ? (rated / total) * 100 : 0;

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-gray-700">
        Card {current + 1} of {total}
      </p>

      <div className="h-2 w-full rounded-full bg-gray-200">
        <div
          className="h-2 rounded-full bg-blue-500 transition-all duration-300"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      <div className="flex gap-3">
        <span className="text-xs text-green-600 font-medium">
          Easy: {stats.easy}
        </span>
        <span className="text-xs text-yellow-600 font-medium">
          Medium: {stats.medium}
        </span>
        <span className="text-xs text-red-600 font-medium">
          Hard: {stats.hard}
        </span>
      </div>
    </div>
  );
}
