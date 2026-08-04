"use client";

import { cn } from "@/lib/utils";
import type { RiskSeverity } from "@/types/analysis";

const CONFIG: Record<RiskSeverity, { label: string; classes: string }> = {
  high: {
    label: "High Risk",
    classes: "bg-red-100 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-400",
  },
  medium: {
    label: "Medium Risk",
    classes: "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400",
  },
  low: {
    label: "Low Risk",
    classes: "bg-green-100 text-green-700 border-green-200 dark:bg-green-950/40 dark:text-green-400",
  },
};

interface RiskBadgeProps {
  severity: RiskSeverity;
  className?: string;
}

export function RiskBadge({ severity, className }: RiskBadgeProps) {
  const { label, classes } = CONFIG[severity];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold",
        classes,
        className,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {label}
    </span>
  );
}
