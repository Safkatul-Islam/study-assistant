"use client";

import { useCallback, useEffect, useState } from "react";

import { FlashcardCard } from "@/components/workspace/flashcard-card";
import { DifficultyRating } from "@/components/workspace/difficulty-rating";
import { StudyProgress } from "@/components/workspace/study-progress";
import { useUpdateFlashcard } from "@/hooks/use-flashcards";
import type { Flashcard, FlashcardStats } from "@/types/api";

interface StudyModeProps {
  documentId: string;
  flashcards: Flashcard[];
  stats: FlashcardStats;
}

export function StudyMode({ documentId, flashcards: initialFlashcards, stats: initialStats }: StudyModeProps) {
  const [cards, setCards] = useState<Flashcard[]>(initialFlashcards);
  const [stats, setStats] = useState<FlashcardStats>(initialStats);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);

  const updateFlashcard = useUpdateFlashcard(documentId);

  // Sync when props change (e.g. after refetch)
  useEffect(() => {
    setCards(initialFlashcards);
  }, [initialFlashcards]);

  useEffect(() => {
    setStats(initialStats);
  }, [initialStats]);

  const currentCard = cards[currentIndex];

  const goNext = useCallback(() => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev + 1) % cards.length);
  }, [cards.length]);

  const goPrev = useCallback(() => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev - 1 + cards.length) % cards.length);
  }, [cards.length]);

  const handleRate = useCallback((difficulty: string) => {
    if (!currentCard) return;

    const oldDifficulty = currentCard.difficulty;
    const newDifficulty = difficulty as Flashcard["difficulty"];

    // Update locally
    setCards((prev) =>
      prev.map((c) =>
        c.id === currentCard.id ? { ...c, difficulty: newDifficulty } : c
      )
    );

    // Update stats locally
    setStats((prev) => {
      const updated = { ...prev };
      if (oldDifficulty !== "unrated") {
        updated[oldDifficulty] = Math.max(0, updated[oldDifficulty] - 1);
      } else {
        updated.unrated = Math.max(0, updated.unrated - 1);
      }
      updated[newDifficulty] = updated[newDifficulty] + 1;
      return updated;
    });

    // Persist to server
    updateFlashcard.mutate({
      flashcardId: currentCard.id,
      difficulty: newDifficulty,
    });

    // Auto-advance after delay
    setTimeout(() => {
      goNext();
    }, 300);
  }, [currentCard, goNext, updateFlashcard]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input
      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") return;

      switch (e.key) {
        case " ":
        case "Enter":
          e.preventDefault();
          setIsFlipped((prev) => !prev);
          break;
        case "ArrowRight":
        case "j":
          e.preventDefault();
          goNext();
          break;
        case "ArrowLeft":
        case "k":
          e.preventDefault();
          goPrev();
          break;
        case "1":
          if (isFlipped) handleRate("easy");
          break;
        case "2":
          if (isFlipped) handleRate("medium");
          break;
        case "3":
          if (isFlipped) handleRate("hard");
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [goNext, goPrev, handleRate, isFlipped]);

  if (!currentCard) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-400">No flashcards to study.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-6 h-full">
      <div className="w-full">
        <StudyProgress current={currentIndex} total={cards.length} stats={stats} />
      </div>

      <div className="flex-1 flex items-center justify-center w-full max-w-lg">
        <FlashcardCard
          flashcard={currentCard}
          isFlipped={isFlipped}
          onFlip={() => setIsFlipped((prev) => !prev)}
        />
      </div>

      {/* Navigation */}
      <div className="flex items-center gap-4">
        <button
          onClick={goPrev}
          className="p-2 rounded-lg hover:bg-gray-100 text-gray-600 transition-colors"
          aria-label="Previous card"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <span className="text-sm text-gray-500">
          {currentIndex + 1} / {cards.length}
        </span>
        <button
          onClick={goNext}
          className="p-2 rounded-lg hover:bg-gray-100 text-gray-600 transition-colors"
          aria-label="Next card"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>

      {/* Difficulty rating */}
      <DifficultyRating
        onRate={handleRate}
        currentDifficulty={currentCard.difficulty}
        disabled={updateFlashcard.isPending}
        visible={isFlipped}
      />

      {/* Keyboard hints */}
      <p className="text-xs text-gray-400 text-center pb-2">
        Space to flip &middot; 1/2/3 to rate &middot; &larr;&rarr; to navigate
      </p>
    </div>
  );
}
