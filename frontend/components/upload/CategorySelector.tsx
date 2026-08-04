"use client";

import { DOC_CATEGORY_LABELS, type DocCategory } from "@/types/document";
import { cn } from "@/lib/utils";

const CATEGORIES: { value: DocCategory; label: string; description: string }[] = [
  { value: "legal", label: "Legal", description: "Contracts, agreements, court documents" },
  { value: "medical", label: "Medical", description: "Reports, prescriptions, insurance forms" },
  { value: "government", label: "Government", description: "Forms, notices, official letters" },
  { value: "financial", label: "Financial", description: "Statements, tax forms, loan documents" },
  { value: "other", label: "Other", description: "Any other document type" },
];

interface CategorySelectorProps {
  value: DocCategory;
  onChange: (value: DocCategory) => void;
  disabled?: boolean;
}

export function CategorySelector({ value, onChange, disabled = false }: CategorySelectorProps) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {CATEGORIES.map((cat) => (
        <button
          key={cat.value}
          type="button"
          disabled={disabled}
          onClick={() => onChange(cat.value)}
          className={cn(
            "flex flex-col items-start rounded-lg border px-3 py-2.5 text-left text-sm transition-colors",
            value === cat.value
              ? "border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-300"
              : "border-border hover:border-blue-300 hover:bg-muted/40",
            disabled && "pointer-events-none opacity-50"
          )}
        >
          <span className="font-medium">{cat.label}</span>
          <span className="mt-0.5 text-xs text-muted-foreground">{cat.description}</span>
        </button>
      ))}
    </div>
  );
}
