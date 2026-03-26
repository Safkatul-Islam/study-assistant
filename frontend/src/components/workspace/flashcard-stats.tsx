"use client";

import type { FlashcardStats } from "@/types/api";

interface FlashcardStatsDisplayProps {
  stats: FlashcardStats;
}

export function FlashcardStatsDisplay({ stats }: FlashcardStatsDisplayProps) {
  const rated = stats.easy + stats.medium + stats.hard;
  const ratedPercent = stats.total > 0 ? Math.round((rated / stats.total) * 100) : 0;

  const boxes = [
    { label: "Total", value: stats.total, bg: "bg-gray-50", text: "text-gray-900" },
    { label: "Easy", value: stats.easy, bg: "bg-green-50", text: "text-green-700" },
    { label: "Medium", value: stats.medium, bg: "bg-yellow-50", text: "text-yellow-800" },
    { label: "Hard", value: stats.hard, bg: "bg-red-50", text: "text-red-700" },
  ];

  return (
    <div className="space-y-2">
      <div className="flex gap-4">
        {boxes.map((box) => (
          <div
            key={box.label}
            className={`flex-1 p-4 rounded-lg border text-center ${box.bg}`}
          >
            <p className={`text-2xl font-bold ${box.text}`}>{box.value}</p>
            <p className="text-sm text-gray-500">{box.label}</p>
          </div>
        ))}
      </div>
      <p className="text-sm text-gray-500 text-center">
        {ratedPercent}% rated
      </p>
    </div>
  );
}
