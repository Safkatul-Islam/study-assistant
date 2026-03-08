"use client";

import { createContext, useCallback, useEffect, useState, type ReactNode } from "react";
import type { User } from "@/types/api";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Hydrate from localStorage
    const storedUser = localStorage.getItem("user");
    const accessToken = localStorage.getItem("access_token");
    if (storedUser && accessToken) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        localStorage.removeItem("user");
      }
    }
    setIsLoading(false);
  }, []);

  const setAuth = useCallback((user: User, accessToken: string, refreshToken: string) => {
    localStorage.setItem("user", JSON.stringify(user));
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    setUser(user);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("user");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, setAuth, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
