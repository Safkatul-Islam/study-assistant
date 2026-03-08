"use client";

import { AnimatePresence } from "framer-motion";
import { useDocuments } from "@/hooks/use-documents";
import { DocumentCard } from "@/components/documents/document-card";
import { DocumentListSkeleton } from "@/components/documents/document-list-skeleton";
import { ErrorMessage } from "@/components/ui/error-message";

export function DocumentList() {
  const { data: documents, isLoading, error } = useDocuments();

  if (isLoading) {
    return <DocumentListSkeleton />;
  }

  if (error) {
    return <ErrorMessage message="Failed to load documents. Please try again." />;
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="rounded-xl border-2 border-dashed border-gray-300 py-12 text-center">
        <p className="text-gray-500">No documents yet. Upload a PDF to get started.</p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <AnimatePresence>
        {documents.map((doc) => (
          <DocumentCard key={doc.id} document={doc} />
        ))}
      </AnimatePresence>
    </div>
  );
}
