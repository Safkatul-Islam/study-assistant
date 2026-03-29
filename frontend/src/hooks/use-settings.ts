"use client";

import { useMutation } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";

export function useUpdateProfile() {
  const { setAuth } = useAuth();

  return useMutation({
    mutationFn: async (full_name: string) => {
      const { data } = await api.patch("/auth/me", { full_name });
      return data;
    },
    onSuccess: (data) => {
      const accessToken = localStorage.getItem("access_token") || "";
      const refreshToken = localStorage.getItem("refresh_token") || "";
      if (data.user) {
        setAuth(data.user, accessToken, refreshToken);
      }
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: async ({
      currentPassword,
      newPassword,
    }: {
      currentPassword: string;
      newPassword: string;
    }) => {
      const { data } = await api.put("/auth/me/password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      return data;
    },
  });
}
