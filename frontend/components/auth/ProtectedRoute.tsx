"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import { authApi } from "@/lib/api/auth";
import { setAccessToken } from "@/lib/api/client";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, fetchProfile } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated && !isLoading) {
      // Try to silently restore session via refresh token cookie
      authApi
        .refreshToken()
        .then(({ data }) => {
          setAccessToken(data.data.access);
          return fetchProfile();
        })
        .catch(() => {
          router.replace("/login");
        });
    }
  }, [isAuthenticated, isLoading, fetchProfile, router]);

  if (isLoading || (!isAuthenticated)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return <>{children}</>;
}
