"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import api from "@/lib/api";
import { cn } from "@/lib/utils";
import { SummaryPanel } from "@/components/workspace/summary-panel";
import { ChatPanel } from "@/components/workspace/chat-panel";
import { PracticePanel } from "@/components/workspace/practice-panel";
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
    <main className="flex h-screen">
      {/* Left: PDF Viewer placeholder */}
      <aside className="w-1/2 border-r bg-gray-50 flex items-center justify-center">
        <p className="text-gray-400">PDF Viewer</p>
      </aside>

      {/* Right: Tabbed workspace */}
      <section className="w-1/2 flex flex-col h-full">
        {/* Header */}
        <div className="p-6 pb-0">
          <h2 className="text-lg font-semibold text-gray-900 truncate">
            {document?.title || "Loading..."}
          </h2>

          {/* Tabs */}
          <nav className="flex gap-4 mt-4 border-b">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "pb-2 text-sm font-medium transition-colors -mb-px",
                  activeTab === tab.id
                    ? "text-black border-b-2 border-black"
                    : "text-gray-500 hover:text-gray-700"
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
              <p className="text-gray-500">
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
