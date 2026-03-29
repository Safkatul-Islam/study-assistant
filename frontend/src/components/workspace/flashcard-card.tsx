"use client";

import { motion } from "framer-motion";

import type { Flashcard } from "@/types/api";

interface FlashcardCardProps {
  flashcard: Flashcard;
  isFlipped: boolean;
  onFlip: () => void;
}

export function FlashcardCard({ flashcard, isFlipped, onFlip }: FlashcardCardProps) {
  return (
    <div
      style={{ perspective: 1000 }}
      className="w-full cursor-pointer"
      onClick={onFlip}
    >
      <motion.div
        animate={{ rotateY: isFlipped ? 180 : 0 }}
        transition={{ type: "spring", stiffness: 260, damping: 20 }}
        style={{ transformStyle: "preserve-3d" }}
        className="relative w-full min-h-[300px]"
      >
        {/* Front face */}
        <div
          style={{ backfaceVisibility: "hidden" }}
          className="absolute inset-0 flex items-center justify-center bg-white dark:bg-gray-800 rounded-2xl shadow-lg border dark:border-gray-700 p-8"
        >
          <p className="text-lg text-gray-900 dark:text-gray-100 text-center whitespace-pre-wrap">
            {flashcard.front}
          </p>
        </div>

        {/* Back face */}
        <div
          style={{ backfaceVisibility: "hidden", transform: "rotateY(180deg)" }}
          className="absolute inset-0 flex items-center justify-center bg-blue-50 dark:bg-blue-900/30 rounded-2xl shadow-lg border border-blue-200 dark:border-blue-800 p-8"
        >
          <p className="text-lg text-gray-900 dark:text-gray-100 text-center whitespace-pre-wrap">
            {flashcard.back}
          </p>
        </div>
      </motion.div>
    </div>
  );
}
