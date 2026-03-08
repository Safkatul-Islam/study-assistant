"use client";

import { motion } from "framer-motion";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

export function AppHeader() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <motion.header
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-sm"
    >
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <span className="text-lg font-bold text-gray-900">StudyForge</span>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-600">{user?.full_name}</span>
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            Log out
          </Button>
        </div>
      </div>
    </motion.header>
  );
}
