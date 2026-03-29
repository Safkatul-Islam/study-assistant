"use client";

import { cn } from "@/lib/utils";
import type { FlashcardStats } from "@/types/api";

interface DifficultyFilterProps {
  selected: string;
  onChange: (value: string) => void;
  stats: FlashcardStats;
}

export function DifficultyFilter({ selected, onChange, stats }: DifficultyFilterProps) {
  const options = [
    { value: "all", label: "All", count: stats.total },
    { value: "unrated", label: "Unrated", count: stats.unrated },
    { value: "easy", label: "Easy", count: stats.easy },
    { value: "medium", label: "Medium", count: stats.medium },
    { value: "hard", label: "Hard", count: stats.hard },
  ];

  return (
    <div className="flex gap-2 flex-wrap">
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={cn(
            "rounded-full px-3 py-1 text-sm font-medium cursor-pointer transition-colors",
            selected === opt.value
              ? "bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900"
              : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
          )}
        >
          {opt.label} ({opt.count})
        </button>
      ))}
    </div>
  );
}
