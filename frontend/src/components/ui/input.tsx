"use client";

import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, id, ...props }, ref) => {
    return (
      <div className="space-y-1">
        {label && (
          <label htmlFor={id} className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className={cn(
            "block w-full rounded-lg border px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-1 dark:bg-gray-800 dark:text-gray-100 dark:focus:ring-offset-gray-900",
            error
              ? "border-red-300 dark:border-red-600 focus:border-red-500 focus:ring-red-500"
              : "border-gray-300 dark:border-gray-600 focus:border-blue-500 focus:ring-blue-500 dark:focus:ring-blue-400",
            className
          )}
          {...props}
        />
        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
export type { InputProps };
