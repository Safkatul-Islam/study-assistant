"use client";

import { UploadButton } from "@/components/documents/upload-button";
import { DocumentList } from "@/components/documents/document-list";

export default function DocumentsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">My Documents</h1>
        <UploadButton />
      </div>
      <DocumentList />
    </div>
  );
}
