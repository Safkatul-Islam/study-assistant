"use client";

import { useState } from "react";

import type { Citation } from "@/types/api";

interface CitationBadgeProps {
  citation: Citation;
}

export function CitationBadge({ citation }: CitationBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  const label =
    citation.page_start && citation.page_end && citation.page_start !== citation.page_end
      ? `p.${citation.page_start}-${citation.page_end}`
      : citation.page_start
        ? `p.${citation.page_start}`
        : "ref";

  return (
    <span
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <button
        type="button"
        onClick={() => {
          if (citation.page_start) {
            window.dispatchEvent(
              new CustomEvent("citation-navigate", {
                detail: { page: citation.page_start },
              })
            );
          }
        }}
        className="inline-flex items-center rounded-full bg-blue-100 dark:bg-blue-900/40 px-2 py-0.5 text-xs font-medium text-blue-700 dark:text-blue-300 cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-900/60 transition-colors"
      >
        [{label}]
      </button>
      {showTooltip && (
        <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 rounded-lg bg-gray-900 dark:bg-gray-700 px-3 py-2 text-xs text-white shadow-lg z-10">
          {citation.snippet}
        </span>
      )}
    </span>
  );
}
