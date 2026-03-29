"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import api from "@/lib/api";
import { cn } from "@/lib/utils";
import { SummaryPanel } from "@/components/workspace/summary-panel";
import { ChatPanel } from "@/components/workspace/chat-panel";
import { PracticePanel } from "@/components/workspace/practice-panel";
import { PdfViewer } from "@/components/workspace/pdf-viewer";
import type { Document } from "@/types/api";

type Tab = "summary" | "chat" | "practice";

const tabs: { id: Tab; label: string }[] = [
  { id: "summary", label: "Summary" },
  { id: "chat", label: "Chat" },
  { id: "practice", label: "Practice" },
];

export default function WorkspacePage() {
  const params = useParams();
  const documentId = params.id as string;
  const [activeTab, setActiveTab] = useState<Tab>("summary");
  const [showPdf, setShowPdf] = useState(true);

  const { data: document } = useQuery({
    queryKey: ["document", documentId],
    queryFn: async () => {
      const { data } = await api.get<{ ok: boolean; document: Document }>(
        `/documents/${documentId}`
      );
      return data.document;
    },
    enabled: !!documentId,
  });

  const isReady = document?.status === "ready";

  return (
    <main className="flex h-screen flex-col md:flex-row">
      {/* PDF Viewer — hidden on mobile, toggleable on desktop */}
      {showPdf && (
        <aside className="hidden md:flex md:w-1/2 border-r border-gray-200 dark:border-gray-700 flex-col">
          {isReady ? (
            <PdfViewer documentId={documentId} />
          ) : (
            <div className="flex flex-1 items-center justify-center bg-gray-50 dark:bg-gray-900">
              <p className="text-gray-400 dark:text-gray-500">
                PDF available when document is ready
              </p>
            </div>
          )}
        </aside>
      )}

      {/* Tabbed workspace */}
      <section
        className={cn(
          "flex flex-col h-full w-full",
          showPdf ? "md:w-1/2" : "md:w-full"
        )}
      >
        {/* Header */}
        <div className="p-6 pb-0">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 truncate">
              {document?.title || "Loading..."}
            </h2>
            <button
              onClick={() => setShowPdf((s) => !s)}
              className="hidden md:inline-flex rounded-md p-1.5 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
              title={showPdf ? "Hide PDF" : "Show PDF"}
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                {showPdf ? (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>

          {/* Tabs */}
          <nav className="flex gap-4 mt-4 border-b dark:border-gray-700">
            {/* Mobile: PDF tab */}
            <button
              onClick={() => setShowPdf((s) => !s)}
              className="pb-2 text-sm font-medium transition-colors -mb-px text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 md:hidden"
            >
              PDF
            </button>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "pb-2 text-sm font-medium transition-colors -mb-px",
                  activeTab === tab.id
                    ? "text-black dark:text-white border-b-2 border-black dark:border-white"
                    : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                )}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-y-auto p-6">
          {!isReady ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-500 dark:text-gray-400">
                {document?.status === "processing"
                  ? "Document is still processing..."
                  : document?.status === "failed"
                    ? `Processing failed: ${document.error_message || "Unknown error"}`
                    : "Loading document..."}
              </p>
            </div>
          ) : (
            <>
              {activeTab === "summary" && <SummaryPanel documentId={documentId} />}
              {activeTab === "chat" && <ChatPanel documentId={documentId} />}
              {activeTab === "practice" && <PracticePanel documentId={documentId} />}
            </>
          )}
        </div>
      </section>
    </main>
  );
}
