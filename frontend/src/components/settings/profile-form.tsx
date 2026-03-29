"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/use-auth";
import { useUpdateProfile } from "@/hooks/use-settings";
import { getApiErrorMessage } from "@/lib/utils";

export function ProfileForm() {
  const { user } = useAuth();
  const updateProfile = useUpdateProfile();

  const [fullName, setFullName] = useState(user?.full_name ?? "");

  const isDirty = fullName.trim() !== (user?.full_name ?? "");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const trimmed = fullName.trim();
    if (!trimmed) {
      toast.error("Name cannot be empty");
      return;
    }

    updateProfile.mutate(trimmed, {
      onSuccess: () => {
        toast.success("Profile updated");
      },
      onError: (error) => {
        toast.error(getApiErrorMessage(error) ?? "Failed to update profile");
      },
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        id="full-name"
        label="Full Name"
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
        className="dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
      />

      <Input
        id="email"
        label="Email"
        value={user?.email ?? ""}
        readOnly
        disabled
        className="bg-gray-50 text-gray-500 dark:bg-gray-700/50 dark:text-gray-400 dark:border-gray-600"
      />

      <div className="flex justify-end">
        <Button
          type="submit"
          isLoading={updateProfile.isPending}
          disabled={!isDirty}
        >
          Save Changes
        </Button>
      </div>
    </form>
  );
}
