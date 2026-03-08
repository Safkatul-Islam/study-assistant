"use client";

import { RegisterForm } from "@/components/auth/register-form";

export default function RegisterPage() {
  return (
    <>
      <h1 className="text-2xl font-bold text-center">Create your account</h1>
      <RegisterForm />
    </>
  );
}
