"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import type { Document } from "@/types/api";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatFileSize, formatDate } from "@/lib/utils";

interface DocumentCardProps {
  document: Document;
}

export function DocumentCard({ document }: DocumentCardProps) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
    >
      <Link
        href={`/documents/${document.id}`}
        className="block rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
      >
        <div className="flex items-start justify-between">
          <h3 className="font-semibold text-gray-900 truncate pr-2">{document.title}</h3>
          <StatusBadge status={document.status} />
        </div>
        <div className="mt-3 flex items-center gap-3 text-xs text-gray-500">
          <span>{formatFileSize(document.file_size)}</span>
          <span>{formatDate(document.created_at)}</span>
        </div>
      </Link>
    </motion.div>
  );
}
