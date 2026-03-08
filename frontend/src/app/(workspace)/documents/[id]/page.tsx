"use client";

import { useParams } from "next/navigation";

export default function WorkspacePage() {
  const params = useParams();
  const documentId = params.id as string;

  return (
    <main className="flex min-h-screen">
      {/* Left: PDF Viewer — implementation in M3 */}
      <aside className="w-1/2 border-r bg-gray-50 flex items-center justify-center">
        <p className="text-gray-400">PDF Viewer</p>
      </aside>

      {/* Right: Tabs (Summary / Chat / Practice) */}
      <section className="w-1/2 p-6">
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Workspace: {documentId}</h2>
          <nav className="flex gap-4 border-b pb-2">
            <button className="font-medium text-black border-b-2 border-black pb-1">
              Summary
            </button>
            <button className="text-gray-500 pb-1">Chat</button>
            <button className="text-gray-500 pb-1">Practice</button>
          </nav>
          {/* Tab content — implementation in M3/M4 */}
          <p className="text-gray-500">Workspace content coming in M3</p>
        </div>
      </section>
    </main>
  );
}
