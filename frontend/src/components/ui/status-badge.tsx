"use client";

import { cn } from "@/lib/utils";

const statusConfig = {
  uploaded: { label: "Uploaded", className: "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300" },
  processing: { label: "Processing", className: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300 animate-pulse" },
  ready: { label: "Ready", className: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300" },
  failed: { label: "Failed", className: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300" },
};

interface StatusBadgeProps {
  status: keyof typeof statusConfig;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status];
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        config.className
      )}
    >
      {config.label}
    </span>
  );
}
