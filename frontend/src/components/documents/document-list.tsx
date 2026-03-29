"use client";

import { useState, useMemo } from "react";
import { AnimatePresence } from "framer-motion";
import { useDocuments } from "@/hooks/use-documents";
import { DocumentCard } from "@/components/documents/document-card";
import { DocumentListSkeleton } from "@/components/documents/document-list-skeleton";
import { ErrorMessage } from "@/components/ui/error-message";
import type { Document } from "@/types/api";

type SortOption = "newest" | "oldest" | "name-asc" | "name-desc";
type StatusFilter = "all" | "processing" | "ready" | "failed";

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: "newest", label: "Newest" },
  { value: "oldest", label: "Oldest" },
  { value: "name-asc", label: "Name A-Z" },
  { value: "name-desc", label: "Name Z-A" },
];

const STATUS_FILTERS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "processing", label: "Processing" },
  { value: "ready", label: "Ready" },
  { value: "failed", label: "Failed" },
];

function filterAndSort(
  documents: Document[],
  search: string,
  sort: SortOption,
  status: StatusFilter
): Document[] {
  const searchLower = search.toLowerCase();

  const filtered = documents.filter((doc) => {
    if (searchLower && !doc.title.toLowerCase().includes(searchLower)) {
      return false;
    }
    if (status !== "all" && doc.status !== status) {
      return false;
    }
    return true;
  });

  const sorted = [...filtered];
  switch (sort) {
    case "newest":
      sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      break;
    case "oldest":
      sorted.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
      break;
    case "name-asc":
      sorted.sort((a, b) => a.title.localeCompare(b.title));
      break;
    case "name-desc":
      sorted.sort((a, b) => b.title.localeCompare(a.title));
      break;
  }

  return sorted;
}

export function DocumentList() {
  const { data: documents, isLoading, error } = useDocuments();
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<SortOption>("newest");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  const filteredDocuments = useMemo(() => {
    if (!documents) return [];
    return filterAndSort(documents, search, sort, statusFilter);
  }, [documents, search, sort, statusFilter]);

  if (isLoading) {
    return <DocumentListSkeleton />;
  }

  if (error) {
    return <ErrorMessage message="Failed to load documents. Please try again." />;
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="rounded-xl border-2 border-dashed border-gray-300 py-12 text-center dark:border-gray-600">
        <p className="text-gray-500 dark:text-gray-400">
          No documents yet. Upload a PDF to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search, Sort, and Filter Controls */}
      <div className="space-y-3">
        <div className="flex flex-col gap-3 sm:flex-row">
          {/* Search input */}
          <div className="relative flex-1">
            <svg
              className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400 dark:text-gray-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search documents..."
              className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-10 pr-4 text-sm text-gray-900 outline-none placeholder:text-gray-400 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 dark:placeholder:text-gray-500 dark:focus:border-indigo-600 dark:focus:ring-indigo-900/30"
            />
          </div>

          {/* Sort dropdown */}
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as SortOption)}
            className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 outline-none focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:focus:border-indigo-600 dark:focus:ring-indigo-900/30"
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Status filter chips */}
        <div className="flex flex-wrap gap-2">
          {STATUS_FILTERS.map((filter) => (
            <button
              key={filter.value}
              onClick={() => setStatusFilter(filter.value)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                statusFilter === filter.value
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {filteredDocuments.length === 0 ? (
        <div className="rounded-xl border-2 border-dashed border-gray-300 py-8 text-center dark:border-gray-600">
          <p className="text-gray-500 dark:text-gray-400">
            No documents match your filters.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <AnimatePresence>
            {filteredDocuments.map((doc) => (
              <DocumentCard key={doc.id} document={doc} />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
