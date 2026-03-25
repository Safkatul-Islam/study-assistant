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
      <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 cursor-help">
        [{label}]
      </span>
      {showTooltip && (
        <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 rounded-lg bg-gray-900 px-3 py-2 text-xs text-white shadow-lg z-10">
          {citation.snippet}
        </span>
      )}
    </span>
  );
}
