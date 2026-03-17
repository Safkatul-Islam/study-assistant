"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRegisterMutation } from "@/hooks/use-auth-mutations";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ErrorMessage } from "@/components/ui/error-message";
import { getApiErrorMessage } from "@/lib/utils";

export function RegisterForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [clientError, setClientError] = useState<string | null>(null);
  const register = useRegisterMutation();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setClientError(null);

    if (password.length < 8) {
      setClientError("Password must be at least 8 characters");
      return;
    }

    register.mutate({ email, password, full_name: fullName });
  };

  const serverError = register.error ? getApiErrorMessage(register.error) : null;

  const errorMessage = clientError || serverError;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {errorMessage && <ErrorMessage message={errorMessage} />}
      <Input
        id="fullName"
        label="Full name"
        type="text"
        placeholder="John Doe"
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
        required
      />
      <Input
        id="email"
        label="Email"
        type="email"
        placeholder="you@example.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <Input
        id="password"
        label="Password"
        type="password"
        placeholder="At least 8 characters"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        minLength={8}
      />
      <Button type="submit" className="w-full" isLoading={register.isPending}>
        Create account
      </Button>
      <p className="text-center text-sm text-gray-600">
        Already have an account?{" "}
        <Link href="/login" className="text-blue-600 hover:underline">
          Sign in
        </Link>
      </p>
    </form>
  );
}
