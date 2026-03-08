"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import api from "@/lib/api";
import type { InitUploadResponse } from "@/types/api";

type UploadStep = "idle" | "init" | "uploading" | "completing" | "done" | "error";

interface UploadState {
  step: UploadStep;
  progress: number;
  error: string | null;
}

export function useUpload() {
  const queryClient = useQueryClient();
  const [state, setState] = useState<UploadState>({
    step: "idle",
    progress: 0,
    error: null,
  });

  const upload = async (file: File) => {
    try {
      // Step 1: Init upload
      setState({ step: "init", progress: 0, error: null });
      const { data } = await api.post<InitUploadResponse>("/documents/init-upload", {
        file_name: file.name,
        file_size: file.size,
        content_type: file.type || "application/pdf",
      });

      // Step 2: Upload to S3 (direct PUT, not through api instance)
      setState({ step: "uploading", progress: 0, error: null });
      await axios.put(data.upload_url, file, {
        headers: { "Content-Type": file.type || "application/pdf" },
        onUploadProgress: (event) => {
          if (event.total) {
            const progress = Math.round((event.loaded / event.total) * 100);
            setState((prev) => ({ ...prev, progress }));
          }
        },
      });

      // Step 3: Complete upload
      setState({ step: "completing", progress: 100, error: null });
      await api.post("/documents/complete-upload", {
        document_id: data.document_id,
      });

      setState({ step: "done", progress: 100, error: null });
      queryClient.invalidateQueries({ queryKey: ["documents"] });

      // Reset after a brief delay
      setTimeout(() => {
        setState({ step: "idle", progress: 0, error: null });
      }, 2000);
    } catch (err) {
      const message =
        axios.isAxiosError(err)
          ? err.response?.data?.error?.message || err.message
          : "Upload failed";
      setState({ step: "error", progress: 0, error: message });
    }
  };

  const reset = () => setState({ step: "idle", progress: 0, error: null });

  return { ...state, upload, reset };
}
