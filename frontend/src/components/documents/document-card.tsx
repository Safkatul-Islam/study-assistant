"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { toast } from "sonner";
import type { Document } from "@/types/api";
import { StatusBadge } from "@/components/ui/status-badge";
import { DocumentMenu } from "@/components/documents/document-menu";
import { useRenameDocument, useDeleteDocument, useUpdateTags } from "@/hooks/use-documents";
import { formatFileSize, formatDate, getApiErrorMessage } from "@/lib/utils";

interface DocumentCardProps {
  document: Document;
}

type EditMode = "none" | "rename" | "tags" | "delete-confirm";

const TAG_COLORS = [
  "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
  "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300",
  "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
  "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300",
  "bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300",
  "bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300",
];

function getTagColor(tag: string): string {
  let hash = 0;
  for (let i = 0; i < tag.length; i++) {
    hash = tag.charCodeAt(i) + ((hash << 5) - hash);
  }
  return TAG_COLORS[Math.abs(hash) % TAG_COLORS.length];
}

export function DocumentCard({ document }: DocumentCardProps) {
  const [editMode, setEditMode] = useState<EditMode>("none");
  const [renameValue, setRenameValue] = useState(document.title);
  const [tagInput, setTagInput] = useState("");
  const [localTags, setLocalTags] = useState<string[]>(document.tags ?? []);
  const renameInputRef = useRef<HTMLInputElement>(null);
  const tagInputRef = useRef<HTMLInputElement>(null);

  const renameMutation = useRenameDocument();
  const deleteMutation = useDeleteDocument();
  const tagsMutation = useUpdateTags();

  useEffect(() => {
    if (editMode === "rename" && renameInputRef.current) {
      renameInputRef.current.focus();
      renameInputRef.current.select();
    }
    if (editMode === "tags" && tagInputRef.current) {
      tagInputRef.current.focus();
    }
  }, [editMode]);

  useEffect(() => {
    setLocalTags(document.tags ?? []);
  }, [document.tags]);

  function handleStartRename() {
    setRenameValue(document.title);
    setEditMode("rename");
  }

  function handleCancelRename() {
    setRenameValue(document.title);
    setEditMode("none");
  }

  function handleSaveRename() {
    const trimmed = renameValue.trim();
    if (!trimmed || trimmed === document.title) {
      handleCancelRename();
      return;
    }
    renameMutation.mutate(
      { documentId: document.id, title: trimmed },
      {
        onSuccess: () => {
          toast.success("Document renamed");
          setEditMode("none");
        },
        onError: (error) => {
          toast.error(getApiErrorMessage(error) ?? "Failed to rename document");
        },
      }
    );
  }

  function handleStartDelete() {
    setEditMode("delete-confirm");
  }

  function handleConfirmDelete() {
    deleteMutation.mutate(document.id, {
      onSuccess: () => {
        toast.success("Document deleted");
      },
      onError: (error) => {
        toast.error(getApiErrorMessage(error) ?? "Failed to delete document");
        setEditMode("none");
      },
    });
  }

  function handleStartTags() {
    setLocalTags(document.tags ?? []);
    setTagInput("");
    setEditMode("tags");
  }

  function handleAddTag() {
    const trimmed = tagInput.trim().toLowerCase();
    if (!trimmed) return;
    if (localTags.includes(trimmed)) {
      setTagInput("");
      return;
    }
    const updated = [...localTags, trimmed];
    setLocalTags(updated);
    setTagInput("");
  }

  function handleRemoveTag(tag: string) {
    const updated = localTags.filter((t) => t !== tag);
    setLocalTags(updated);
  }

  function handleSaveTags() {
    tagsMutation.mutate(
      { documentId: document.id, tags: localTags },
      {
        onSuccess: () => {
          toast.success("Tags updated");
          setEditMode("none");
        },
        onError: (error) => {
          toast.error(getApiErrorMessage(error) ?? "Failed to update tags");
        },
      }
    );
  }

  const isEditing = editMode !== "none";
  const tags = document.tags ?? [];

  const cardContent = (
    <>
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          {editMode === "rename" ? (
            <input
              ref={renameInputRef}
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSaveRename();
                if (e.key === "Escape") handleCancelRename();
              }}
              onBlur={handleSaveRename}
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
              }}
              disabled={renameMutation.isPending}
              className="w-full rounded-md border border-indigo-300 bg-white px-2 py-1 text-sm font-semibold text-gray-900 outline-none focus:ring-2 focus:ring-indigo-500 dark:border-indigo-600 dark:bg-gray-700 dark:text-gray-100"
            />
          ) : (
            <h3 className="truncate font-semibold text-gray-900 dark:text-gray-100">
              {document.title}
            </h3>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <StatusBadge status={document.status} />
          <DocumentMenu
            onRename={handleStartRename}
            onManageTags={handleStartTags}
            onDelete={handleStartDelete}
          />
        </div>
      </div>

      {/* Tags */}
      {editMode === "tags" ? (
        <div
          className="mt-3 space-y-2"
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
          }}
        >
          <div className="flex flex-wrap gap-1">
            {localTags.map((tag) => (
              <span
                key={tag}
                className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${getTagColor(tag)}`}
              >
                {tag}
                <button
                  onClick={() => handleRemoveTag(tag)}
                  className="ml-0.5 hover:opacity-70"
                  aria-label={`Remove tag ${tag}`}
                >
                  x
                </button>
              </span>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <input
              ref={tagInputRef}
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleAddTag();
                }
                if (e.key === "Escape") setEditMode("none");
              }}
              placeholder="Add tag..."
              className="w-full rounded-md border border-gray-300 bg-white px-2 py-1 text-xs outline-none focus:ring-2 focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleSaveTags}
              disabled={tagsMutation.isPending}
              className="rounded-md bg-indigo-600 px-3 py-1 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {tagsMutation.isPending ? "Saving..." : "Save"}
            </button>
            <button
              onClick={() => setEditMode("none")}
              className="rounded-md px-3 py-1 text-xs font-medium text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : tags.length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-1">
          {tags.map((tag) => (
            <span
              key={tag}
              className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${getTagColor(tag)}`}
            >
              {tag}
            </span>
          ))}
        </div>
      ) : null}

      {/* Delete confirmation */}
      {editMode === "delete-confirm" && (
        <div
          className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-900/20"
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
          }}
        >
          <p className="text-sm text-red-700 dark:text-red-400">
            Delete this document? This cannot be undone.
          </p>
          <div className="mt-2 flex gap-2">
            <button
              onClick={handleConfirmDelete}
              disabled={deleteMutation.isPending}
              className="rounded-md bg-red-600 px-3 py-1 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </button>
            <button
              onClick={() => setEditMode("none")}
              className="rounded-md px-3 py-1 text-xs font-medium text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-3 flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
        <span>{formatFileSize(document.file_size)}</span>
        <span>{formatDate(document.created_at)}</span>
      </div>
    </>
  );

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
    >
      {isEditing ? (
        <div className="block rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          {cardContent}
        </div>
      ) : (
        <Link
          href={`/documents/${document.id}`}
          className="block rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800"
        >
          {cardContent}
        </Link>
      )}
    </motion.div>
  );
}
