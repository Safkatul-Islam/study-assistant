"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";
import type { AuthResponse } from "@/types/api";

interface LoginInput {
  email: string;
  password: string;
}

interface RegisterInput {
  email: string;
  password: string;
  full_name: string;
}

export function useLoginMutation() {
  const auth = useAuth();
  const router = useRouter();

  return useMutation({
    mutationFn: async (input: LoginInput) => {
      const { data } = await api.post<AuthResponse>("/auth/login", input);
      return data;
    },
    onSuccess: (data) => {
      auth.setAuth(data.user, data.access_token, data.refresh_token);
      router.push("/documents");
    },
  });
}

export function useRegisterMutation() {
  const auth = useAuth();
  const router = useRouter();

  return useMutation({
    mutationFn: async (input: RegisterInput) => {
      const { data } = await api.post<AuthResponse>("/auth/register", input);
      return data;
    },
    onSuccess: (data) => {
      auth.setAuth(data.user, data.access_token, data.refresh_token);
      router.push("/documents");
    },
  });
}
