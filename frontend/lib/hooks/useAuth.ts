"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";

export function useAuth() {
  return useAuthStore();
}

export function useRequireAuth() {
  const { isAuthenticated, isLoading, fetchProfile } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      // Try to restore session via refresh token cookie
      fetchProfile().catch(() => {
        router.replace("/login");
      });
    }
  }, [isAuthenticated, isLoading, fetchProfile, router]);

  return { isAuthenticated, isLoading };
}
