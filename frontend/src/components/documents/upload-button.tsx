"use client";

import { useRef } from "react";
import { useUpload } from "@/hooks/use-upload";
import { Button } from "@/components/ui/button";

export function UploadButton() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { step, progress, error, upload, reset } = useUpload();

  const isUploading = step !== "idle" && step !== "done" && step !== "error";

  const handleClick = () => {
    if (step === "error") {
      reset();
    }
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      upload(file);
      // Reset input so same file can be re-selected
      e.target.value = "";
    }
  };

  const label = (() => {
    switch (step) {
      case "init":
        return "Preparing...";
      case "uploading":
        return `Uploading ${progress}%`;
      case "completing":
        return "Finalizing...";
      case "done":
        return "Uploaded!";
      case "error":
        return "Retry Upload";
      default:
        return "Upload PDF";
    }
  })();

  return (
    <div className="flex items-center gap-3">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        className="hidden"
        onChange={handleFileChange}
      />
      <Button onClick={handleClick} isLoading={isUploading} disabled={isUploading}>
        {label}
      </Button>
      {error && <span className="text-sm text-red-600">{error}</span>}
    </div>
  );
}
