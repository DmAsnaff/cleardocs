"use client";

import type { KeyDate } from "@/types/analysis";
import { cn } from "@/lib/utils";

interface DateTimelineProps {
  dates: KeyDate[];
}

function formatDate(date: string | null): string {
  if (!date) return "";
  try {
    return new Intl.DateTimeFormat("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
    }).format(new Date(date));
  } catch {
    return date;
  }
}

function isPast(date: string | null): boolean {
  if (!date) return false;
  try {
    return new Date(date) < new Date();
  } catch {
    return false;
  }
}

export function DateTimeline({ dates }: DateTimelineProps) {
  if (dates.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No key dates identified in this document.</p>
    );
  }

  return (
    <ol className="relative border-l border-border ml-3 space-y-6">
      {dates.map((kd, i) => {
        const past = isPast(kd.date);
        const displayDate = kd.date ? formatDate(kd.date) : kd.relative ?? "—";

        return (
          <li key={i} className="ml-6">
            {/* Dot */}
            <span
              className={cn(
                "absolute -left-2 flex h-4 w-4 items-center justify-center rounded-full ring-2 ring-background",
                past ? "bg-muted-foreground/40" : "bg-blue-500",
              )}
            />

            <div className="space-y-0.5">
              <p
                className={cn(
                  "text-sm font-medium",
                  past && "text-muted-foreground line-through decoration-muted-foreground/50",
                )}
              >
                {kd.label}
              </p>
              <p className={cn("text-xs font-mono", past ? "text-muted-foreground" : "text-blue-600")}>
                {displayDate}
              </p>
              {kd.description && (
                <p className="text-xs text-muted-foreground">{kd.description}</p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
