"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useChangePassword } from "@/hooks/use-settings";
import { getApiErrorMessage } from "@/lib/utils";

interface FormState {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const INITIAL_STATE: FormState = {
  currentPassword: "",
  newPassword: "",
  confirmPassword: "",
};

function validate(form: FormState): Record<string, string> {
  const errors: Record<string, string> = {};

  if (!form.currentPassword) {
    errors.currentPassword = "Current password is required";
  }

  if (!form.newPassword) {
    errors.newPassword = "New password is required";
  } else if (form.newPassword.length < 8) {
    errors.newPassword = "Password must be at least 8 characters";
  }

  if (!form.confirmPassword) {
    errors.confirmPassword = "Please confirm your new password";
  } else if (form.newPassword !== form.confirmPassword) {
    errors.confirmPassword = "Passwords do not match";
  }

  return errors;
}

export function PasswordForm() {
  const changePassword = useChangePassword();

  const [form, setForm] = useState<FormState>(INITIAL_STATE);
  const [errors, setErrors] = useState<Record<string, string>>({});

  function updateField(field: keyof FormState, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    // Clear field error on change
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const validationErrors = validate(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    changePassword.mutate(
      {
        currentPassword: form.currentPassword,
        newPassword: form.newPassword,
      },
      {
        onSuccess: () => {
          toast.success("Password changed successfully");
          setForm(INITIAL_STATE);
          setErrors({});
        },
        onError: (error) => {
          toast.error(
            getApiErrorMessage(error) ?? "Failed to change password"
          );
        },
      }
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        id="current-password"
        label="Current Password"
        type="password"
        value={form.currentPassword}
        onChange={(e) => updateField("currentPassword", e.target.value)}
        error={errors.currentPassword}
        className="dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
      />

      <Input
        id="new-password"
        label="New Password"
        type="password"
        value={form.newPassword}
        onChange={(e) => updateField("newPassword", e.target.value)}
        error={errors.newPassword}
        className="dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
      />

      <Input
        id="confirm-password"
        label="Confirm New Password"
        type="password"
        value={form.confirmPassword}
        onChange={(e) => updateField("confirmPassword", e.target.value)}
        error={errors.confirmPassword}
        className="dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
      />

      <div className="flex justify-end">
        <Button type="submit" isLoading={changePassword.isPending}>
          Change Password
        </Button>
      </div>
    </form>
  );
}
