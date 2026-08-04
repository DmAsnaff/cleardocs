"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { authApi } from "@/lib/api/auth";
import type { User } from "@/types/user";

const LANGUAGE_OPTIONS = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "ar", label: "Arabic" },
  { value: "zh", label: "Chinese (Simplified)" },
  { value: "ja", label: "Japanese" },
  { value: "pt", label: "Portuguese" },
  { value: "hi", label: "Hindi" },
  { value: "ko", label: "Korean" },
];

// ── Alert banner ──────────────────────────────────────────────────────────────

function Alert({
  type,
  message,
  onClose,
}: {
  type: "success" | "error";
  message: string;
  onClose: () => void;
}) {
  const styles =
    type === "success"
      ? "bg-green-50 border-green-200 text-green-800"
      : "bg-red-50 border-red-200 text-red-700";
  return (
    <div className={`flex items-start justify-between p-3 rounded-lg border text-sm ${styles}`}>
      <span>{message}</span>
      <button onClick={onClose} className="ml-3 opacity-60 hover:opacity-100 text-base leading-none">
        ✕
      </button>
    </div>
  );
}

// ── Section wrapper ───────────────────────────────────────────────────────────

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="mb-5">
        <h2 className="text-base font-semibold text-gray-900">{title}</h2>
        {description && <p className="text-sm text-gray-500 mt-0.5">{description}</p>}
      </div>
      {children}
    </div>
  );
}

// ── Delete confirmation dialog ────────────────────────────────────────────────

function DeleteDialog({
  onConfirm,
  onCancel,
  loading,
}: {
  onConfirm: () => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const [text, setText] = useState("");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
        <h3 className="text-base font-semibold text-gray-900 mb-2">Delete account?</h3>
        <p className="text-sm text-gray-600 mb-4">
          This is permanent. All your documents, analyses, and chat history will be deleted within
          30 days and cannot be recovered.
        </p>
        <p className="text-sm font-medium text-gray-700 mb-2">
          Type <span className="font-mono bg-gray-100 px-1 rounded">DELETE</span> to confirm
        </p>
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="DELETE"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-500 mb-4"
        />
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={text !== "DELETE" || loading}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Deleting…" : "Delete my account"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [loadingUser, setLoadingUser] = useState(true);

  // Profile form
  const [fullName, setFullName] = useState("");
  const [preferredLanguage, setPreferredLanguage] = useState("en");
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileAlert, setProfileAlert] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  // Password form
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newPasswordConfirm, setNewPasswordConfirm] = useState("");
  const [savingPassword, setSavingPassword] = useState(false);
  const [passwordAlert, setPasswordAlert] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  // Data export
  const [exporting, setExporting] = useState(false);

  // Delete account
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deletingAccount, setDeletingAccount] = useState(false);

  useEffect(() => {
    authApi
      .getProfile()
      .then(({ data }) => {
        setUser(data.data);
        setFullName(data.data.full_name ?? "");
        setPreferredLanguage(data.data.preferred_language ?? "en");
      })
      .catch(() => router.replace("/login"))
      .finally(() => setLoadingUser(false));
  }, [router]);

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    setSavingProfile(true);
    setProfileAlert(null);
    try {
      const { data } = await authApi.updateProfile({
        full_name: fullName,
        preferred_language: preferredLanguage,
      });
      setUser(data.data);
      setProfileAlert({ type: "success", msg: "Profile updated." });
    } catch {
      setProfileAlert({ type: "error", msg: "Failed to update profile. Please try again." });
    } finally {
      setSavingProfile(false);
    }
  }

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    if (newPassword !== newPasswordConfirm) {
      setPasswordAlert({ type: "error", msg: "New passwords do not match." });
      return;
    }
    setSavingPassword(true);
    setPasswordAlert(null);
    try {
      await authApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        new_password_confirm: newPasswordConfirm,
      });
      setCurrentPassword("");
      setNewPassword("");
      setNewPasswordConfirm("");
      setPasswordAlert({ type: "success", msg: "Password changed successfully." });
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        "Password change failed. Check your current password.";
      setPasswordAlert({ type: "error", msg });
    } finally {
      setSavingPassword(false);
    }
  }

  async function handleExportData() {
    setExporting(true);
    try {
      const { data } = await authApi.dataExport();
      const url = URL.createObjectURL(data as Blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "my_cleardocs_data.json";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // silently fail — user can retry
    } finally {
      setExporting(false);
    }
  }

  async function handleDeleteAccount() {
    setDeletingAccount(true);
    try {
      await authApi.deleteAccount();
      router.replace("/login");
    } catch {
      setDeletingAccount(false);
      setShowDeleteDialog(false);
    }
  }

  if (loadingUser) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-gray-300 border-t-gray-900 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top nav */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <Link href="/" className="text-lg font-semibold text-gray-900">
            ClearDocs
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/history" className="text-sm text-gray-600 hover:text-gray-900">
              History
            </Link>
            <Link href="/upload" className="text-sm text-gray-600 hover:text-gray-900">
              Upload
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-2xl mx-auto px-4 sm:px-6 py-10 space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

        {/* ── Profile ── */}
        <Section title="Profile" description="Update your display name and language preference.">
          <form onSubmit={handleSaveProfile} className="space-y-4">
            {profileAlert && (
              <Alert
                type={profileAlert.type}
                message={profileAlert.msg}
                onClose={() => setProfileAlert(null)}
              />
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={user?.email ?? ""}
                disabled
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-gray-50 text-gray-500 cursor-not-allowed"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Your name"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Preferred language
              </label>
              <select
                value={preferredLanguage}
                onChange={(e) => setPreferredLanguage(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
              >
                {LANGUAGE_OPTIONS.map((l) => (
                  <option key={l.value} value={l.value}>
                    {l.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Used as the default output language for document translations.
              </p>
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={savingProfile}
                className="px-4 py-2 text-sm font-medium bg-gray-900 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors"
              >
                {savingProfile ? "Saving…" : "Save changes"}
              </button>
            </div>
          </form>
        </Section>

        {/* ── Password ── */}
        <Section title="Password" description="Change your account password.">
          <form onSubmit={handleChangePassword} className="space-y-4">
            {passwordAlert && (
              <Alert
                type={passwordAlert.type}
                message={passwordAlert.msg}
                onClose={() => setPasswordAlert(null)}
              />
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Current password
              </label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                autoComplete="current-password"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">New password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Confirm new password
              </label>
              <input
                type="password"
                value={newPasswordConfirm}
                onChange={(e) => setNewPasswordConfirm(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
              />
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={savingPassword || !currentPassword || !newPassword || !newPasswordConfirm}
                className="px-4 py-2 text-sm font-medium bg-gray-900 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors"
              >
                {savingPassword ? "Saving…" : "Change password"}
              </button>
            </div>
          </form>
        </Section>

        {/* ── Data ── */}
        <Section
          title="Your data"
          description="Download a copy of your data or permanently delete your account."
        >
          <div className="space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-gray-800">Export data</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Download a JSON file containing all your documents, translations, and account info.
                </p>
              </div>
              <button
                onClick={handleExportData}
                disabled={exporting}
                className="shrink-0 px-4 py-2 text-sm font-medium border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
              >
                {exporting ? "Exporting…" : "Export"}
              </button>
            </div>

            <hr className="border-gray-200" />

            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-red-700">Delete account</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Permanently remove your account. All data will be purged within 30 days.
                </p>
              </div>
              <button
                onClick={() => setShowDeleteDialog(true)}
                className="shrink-0 px-4 py-2 text-sm font-medium border border-red-300 rounded-lg text-red-700 hover:bg-red-50 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </Section>
      </main>

      {showDeleteDialog && (
        <DeleteDialog
          onConfirm={handleDeleteAccount}
          onCancel={() => setShowDeleteDialog(false)}
          loading={deletingAccount}
        />
      )}
    </div>
  );
}
