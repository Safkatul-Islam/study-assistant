"use client";

import { AnimatePresence, motion } from "framer-motion";

import { cn } from "@/lib/utils";

interface DifficultyRatingProps {
  onRate: (difficulty: string) => void;
  currentDifficulty: string;
  disabled: boolean;
  visible: boolean;
}

const options = [
  { value: "easy", label: "Easy", key: "1", base: "bg-green-100 text-green-700", active: "ring-2 ring-green-500" },
  { value: "medium", label: "Medium", key: "2", base: "bg-yellow-100 text-yellow-800", active: "ring-2 ring-yellow-500" },
  { value: "hard", label: "Hard", key: "3", base: "bg-red-100 text-red-700", active: "ring-2 ring-red-500" },
];

export function DifficultyRating({ onRate, currentDifficulty, disabled, visible }: DifficultyRatingProps) {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 10 }}
          transition={{ duration: 0.2 }}
          className="flex gap-3 justify-center"
        >
          {options.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onRate(opt.value)}
              disabled={disabled}
              className={cn(
                "flex flex-col items-center rounded-lg px-5 py-2.5 text-sm font-medium transition-colors",
                opt.base,
                currentDifficulty === opt.value && opt.active,
                disabled && "opacity-50 cursor-not-allowed"
              )}
            >
              <span>{opt.label}</span>
              <span className="text-xs opacity-60 mt-0.5">{opt.key}</span>
            </button>
          ))}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
