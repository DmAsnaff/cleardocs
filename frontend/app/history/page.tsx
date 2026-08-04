"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { listDocuments, deleteDocument } from "@/lib/api/documents";
import type { Document, DocCategory, DocumentStatus } from "@/types/document";
import { DOC_CATEGORY_LABELS, STATUS_LABELS } from "@/types/document";

// ── Category filter config ──────────────────────────────────────────────────

const CATEGORY_FILTERS: Array<{ value: string; label: string }> = [
  { value: "", label: "All" },
  { value: "legal", label: "Legal" },
  { value: "medical", label: "Medical" },
  { value: "government", label: "Government" },
  { value: "financial", label: "Financial" },
  { value: "other", label: "Other" },
];

const STATUS_FILTERS: Array<{ value: string; label: string }> = [
  { value: "", label: "All" },
  { value: "done", label: "Done" },
  { value: "analysing", label: "Processing" },
  { value: "failed", label: "Failed" },
];

// ── Status badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: DocumentStatus }) {
  const colors: Record<DocumentStatus, string> = {
    done: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
    pending: "bg-gray-100 text-gray-600",
    validating: "bg-blue-100 text-blue-700",
    extracting: "bg-blue-100 text-blue-700",
    chunking: "bg-blue-100 text-blue-700",
    analysing: "bg-amber-100 text-amber-700",
    translating: "bg-purple-100 text-purple-700",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colors[status]}`}>
      {STATUS_LABELS[status]}
    </span>
  );
}

// ── Category badge ────────────────────────────────────────────────────────────

function CategoryBadge({ category }: { category: DocCategory | null }) {
  if (!category) return null;
  const colors: Record<DocCategory, string> = {
    legal: "bg-indigo-100 text-indigo-700",
    medical: "bg-rose-100 text-rose-700",
    government: "bg-teal-100 text-teal-700",
    financial: "bg-emerald-100 text-emerald-700",
    other: "bg-gray-100 text-gray-600",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colors[category]}`}>
      {DOC_CATEGORY_LABELS[category]}
    </span>
  );
}

// ── Document card ─────────────────────────────────────────────────────────────

function DocumentCard({
  doc,
  onDelete,
}: {
  doc: Document;
  onDelete: (id: string) => void;
}) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const uploadDate = new Date(doc.uploaded_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  async function handleDelete() {
    if (!confirming) {
      setConfirming(true);
      return;
    }
    setDeleting(true);
    try {
      await deleteDocument(doc.id);
      onDelete(doc.id);
    } catch {
      setDeleting(false);
      setConfirming(false);
    }
  }

  const fileIcon =
    doc.mime_type === "application/pdf" ? (
      <svg className="w-8 h-8 text-red-400" fill="currentColor" viewBox="0 0 24 24">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z" />
      </svg>
    ) : (
      <svg className="w-8 h-8 text-blue-400" fill="currentColor" viewBox="0 0 24 24">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 1.5L18.5 9H13V3.5z" />
      </svg>
    );

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 flex flex-col gap-3 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className="shrink-0 mt-0.5">{fileIcon}</div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-gray-900 truncate" title={doc.original_filename}>
            {doc.original_filename}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">
            {doc.file_size_mb} · {uploadDate}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5">
        <StatusBadge status={doc.status} />
        {doc.doc_category && <CategoryBadge category={doc.doc_category as DocCategory} />}
      </div>

      {doc.status === "failed" && doc.error_message && (
        <p className="text-xs text-red-600 line-clamp-2">{doc.error_message}</p>
      )}

      <div className="flex items-center gap-2 pt-1">
        {doc.status === "done" && (
          <Link
            href={`/docs/${doc.id}`}
            className="flex-1 text-center text-xs font-medium bg-gray-900 text-white py-1.5 px-3 rounded-md hover:bg-gray-700 transition-colors"
          >
            View
          </Link>
        )}
        <button
          onClick={handleDelete}
          disabled={deleting}
          className={`${doc.status === "done" ? "" : "flex-1"} text-xs font-medium py-1.5 px-3 rounded-md border transition-colors ${
            confirming
              ? "border-red-500 text-red-600 hover:bg-red-50"
              : "border-gray-300 text-gray-600 hover:bg-gray-50"
          }`}
        >
          {deleting ? "Deleting…" : confirming ? "Confirm?" : "Delete"}
        </button>
        {confirming && !deleting && (
          <button
            onClick={() => setConfirming(false)}
            className="text-xs text-gray-400 hover:text-gray-600"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}

// ── Filter chip ───────────────────────────────────────────────────────────────

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1 text-xs font-medium rounded-full border transition-colors ${
        active
          ? "bg-gray-900 text-white border-gray-900"
          : "bg-white text-gray-600 border-gray-300 hover:border-gray-400"
      }`}
    >
      {label}
    </button>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function HistoryPage() {
  const router = useRouter();

  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | null>(null);

  const [rawSearch, setRawSearch] = useState("");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounce search input
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setSearch(rawSearch.trim()), 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [rawSearch]);

  const fetchDocs = useCallback(
    async (cursor?: string) => {
      const isLoadMore = Boolean(cursor);
      isLoadMore ? setLoadingMore(true) : setLoading(true);

      try {
        const resp = await listDocuments({
          cursor,
          category: category || undefined,
          status: statusFilter || undefined,
          search: search || undefined,
        });

        setDocs((prev) => (isLoadMore ? [...prev, ...resp.results] : resp.results));

        // Extract cursor from next URL
        if (resp.next) {
          const url = new URL(resp.next);
          setNextCursor(url.searchParams.get("cursor"));
        } else {
          setNextCursor(null);
        }
      } catch {
        // Token expired → interceptor redirects to /login
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [category, statusFilter, search]
  );

  // Refetch when filters change
  useEffect(() => {
    setDocs([]);
    setNextCursor(null);
    fetchDocs();
  }, [fetchDocs]);

  function handleDelete(id: string) {
    setDocs((prev) => prev.filter((d) => d.id !== id));
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top nav */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <Link href="/" className="text-lg font-semibold text-gray-900">
            ClearDocs
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/upload" className="text-sm text-gray-600 hover:text-gray-900">
              Upload
            </Link>
            <Link href="/settings" className="text-sm text-gray-600 hover:text-gray-900">
              Settings
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Document History</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {docs.length} document{docs.length !== 1 ? "s" : ""}
            </p>
          </div>
          <Link
            href="/upload"
            className="bg-gray-900 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
          >
            + Upload
          </Link>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            placeholder="Search by filename…"
            value={rawSearch}
            onChange={(e) => setRawSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
          />
          {rawSearch && (
            <button
              onClick={() => setRawSearch("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          )}
        </div>

        {/* Category filter */}
        <div className="flex flex-wrap gap-2 mb-3">
          {CATEGORY_FILTERS.map((f) => (
            <FilterChip
              key={f.value}
              label={f.label}
              active={category === f.value}
              onClick={() => setCategory(f.value)}
            />
          ))}
        </div>

        {/* Status filter */}
        <div className="flex flex-wrap gap-2 mb-6">
          {STATUS_FILTERS.map((f) => (
            <FilterChip
              key={f.value}
              label={f.label}
              active={statusFilter === f.value}
              onClick={() => setStatusFilter(f.value)}
            />
          ))}
        </div>

        {/* Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-white border border-gray-200 rounded-lg p-4 animate-pulse">
                <div className="flex gap-3 mb-3">
                  <div className="w-8 h-8 bg-gray-200 rounded" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 bg-gray-200 rounded w-3/4" />
                    <div className="h-2 bg-gray-200 rounded w-1/2" />
                  </div>
                </div>
                <div className="flex gap-2 mb-3">
                  <div className="h-5 bg-gray-200 rounded-full w-14" />
                  <div className="h-5 bg-gray-200 rounded-full w-16" />
                </div>
                <div className="flex gap-2">
                  <div className="h-7 bg-gray-200 rounded-md flex-1" />
                  <div className="h-7 bg-gray-200 rounded-md w-16" />
                </div>
              </div>
            ))}
          </div>
        ) : docs.length === 0 ? (
          <div className="text-center py-16">
            <svg
              className="mx-auto w-12 h-12 text-gray-300 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p className="text-gray-500 font-medium">No documents found</p>
            <p className="text-gray-400 text-sm mt-1">
              {search || category || statusFilter
                ? "Try adjusting your filters"
                : "Upload your first document to get started"}
            </p>
            {!search && !category && !statusFilter && (
              <Link
                href="/upload"
                className="mt-4 inline-block bg-gray-900 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-gray-700"
              >
                Upload a document
              </Link>
            )}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {docs.map((doc) => (
                <DocumentCard key={doc.id} doc={doc} onDelete={handleDelete} />
              ))}
            </div>

            {nextCursor && (
              <div className="mt-8 text-center">
                <button
                  onClick={() => fetchDocs(nextCursor)}
                  disabled={loadingMore}
                  className="px-6 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
                >
                  {loadingMore ? "Loading…" : "Load more"}
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
