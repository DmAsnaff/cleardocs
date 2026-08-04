"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api/auth";

type State = "verifying" | "success" | "error";

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [state, setState] = useState<State>("verifying");
  const [errorMessage, setErrorMessage] = useState<string>("");

  useEffect(() => {
    if (!token) {
      setState("error");
      setErrorMessage("No verification token found in the URL.");
      return;
    }

    authApi
      .verifyEmail(token)
      .then(() => setState("success"))
      .catch((err) => {
        const msg =
          err?.response?.data?.errors?.token?.[0] ??
          err?.response?.data?.message ??
          "Verification failed. The link may have expired.";
        setErrorMessage(msg);
        setState("error");
      });
  }, [token]);

  if (state === "verifying") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-500 text-sm">Verifying your email…</p>
        </div>
      </div>
    );
  }

  if (state === "success") {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
          <div className="text-5xl mb-4">✅</div>
          <h1 className="text-xl font-semibold text-gray-900 mb-2">Email verified!</h1>
          <p className="text-gray-500 text-sm mb-6">
            Your account is now active. You can sign in and start uploading documents.
          </p>
          <Link
            href="/login"
            className="inline-block bg-blue-600 text-white rounded-lg px-6 py-2.5 text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Sign in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
        <div className="text-5xl mb-4">❌</div>
        <h1 className="text-xl font-semibold text-gray-900 mb-2">Verification failed</h1>
        <p className="text-gray-500 text-sm mb-6">{errorMessage}</p>
        <Link
          href="/register"
          className="inline-block text-sm text-blue-600 font-medium hover:underline"
        >
          Register again
        </Link>
      </div>
    </div>
  );
}
