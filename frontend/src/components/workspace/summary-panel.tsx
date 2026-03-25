"use client";

import { useSummary } from "@/hooks/use-summary";
import { ErrorMessage } from "@/components/ui/error-message";
import { Skeleton } from "@/components/ui/skeleton";
import { getApiErrorMessage } from "@/lib/utils";

interface SummaryPanelProps {
  documentId: string;
}

export function SummaryPanel({ documentId }: SummaryPanelProps) {
  const { data, isLoading, error } = useSummary(documentId);

  if (isLoading) {
    return <SummarySkeleton />;
  }

  if (error) {
    return <ErrorMessage message={getApiErrorMessage(error) || "Failed to load summary"} />;
  }

  if (!data?.summary) {
    return <p className="text-gray-500">No summary available.</p>;
  }

  const { summary } = data;

  return (
    <div className="space-y-6">
      {/* Executive Summary */}
      <section>
        <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
          Executive Summary
        </h3>
        <ul className="space-y-2">
          {summary.executive_summary.map((point, i) => (
            <li key={i} className="flex gap-2 text-sm text-gray-700">
              <span className="text-blue-500 mt-1 shrink-0">&bull;</span>
              <span>{point}</span>
            </li>
          ))}
        </ul>
      </section>

      {/* Key Concepts */}
      <section>
        <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
          Key Concepts
        </h3>
        <div className="flex flex-wrap gap-2">
          {summary.key_concepts.map((concept, i) => (
            <span
              key={i}
              className="inline-flex items-center rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700"
            >
              {concept}
            </span>
          ))}
        </div>
      </section>

      {/* Definitions */}
      {Object.keys(summary.definitions).length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
            Key Definitions
          </h3>
          <dl className="space-y-3">
            {Object.entries(summary.definitions).map(([term, definition]) => (
              <div key={term} className="rounded-lg bg-gray-50 p-3">
                <dt className="text-sm font-medium text-gray-900">{term}</dt>
                <dd className="mt-1 text-sm text-gray-600">{definition}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      {/* Possible Questions */}
      <section>
        <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
          Study Questions
        </h3>
        <ol className="space-y-2 list-decimal list-inside">
          {summary.possible_questions.map((question, i) => (
            <li key={i} className="text-sm text-gray-700">
              {question}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function SummarySkeleton() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-4 w-32 mb-3" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-4/6" />
        </div>
      </div>
      <div>
        <Skeleton className="h-4 w-28 mb-3" />
        <div className="flex gap-2">
          <Skeleton className="h-6 w-20 rounded-full" />
          <Skeleton className="h-6 w-24 rounded-full" />
          <Skeleton className="h-6 w-16 rounded-full" />
        </div>
      </div>
      <div>
        <Skeleton className="h-4 w-28 mb-3" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full mt-2" />
      </div>
    </div>
  );
}
