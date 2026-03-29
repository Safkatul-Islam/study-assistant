"use client";

import { ProfileForm } from "@/components/settings/profile-form";
import { PasswordForm } from "@/components/settings/password-form";
import { ThemeSelector } from "@/components/settings/theme-selector";

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        Settings
      </h1>

      <div className="mt-8 space-y-8">
        {/* Profile Section */}
        <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Profile
          </h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Update your display name.
          </p>
          <div className="mt-4">
            <ProfileForm />
          </div>
        </section>

        {/* Password Section */}
        <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Password
          </h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Change your account password.
          </p>
          <div className="mt-4">
            <PasswordForm />
          </div>
        </section>

        {/* Appearance Section */}
        <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Appearance
          </h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Choose your preferred theme.
          </p>
          <div className="mt-4">
            <ThemeSelector />
          </div>
        </section>
      </div>
    </div>
  );
}
