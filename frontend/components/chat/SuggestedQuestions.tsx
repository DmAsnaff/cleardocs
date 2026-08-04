"use client";

import type { DocCategory } from "@/types/document";

const SUGGESTIONS: Record<DocCategory, string[]> = {
  legal: [
    "What are my main obligations under this agreement?",
    "What are the termination conditions?",
    "Are there any penalty or liability clauses I should know about?",
    "What are the governing law and dispute resolution terms?",
  ],
  medical: [
    "What are the key findings in this document?",
    "What follow-up actions or appointments are required?",
    "What medications or treatments are mentioned?",
    "Are there any contraindications or warnings?",
  ],
  government: [
    "What deadlines or response dates apply to me?",
    "What action is required on my part?",
    "What are the consequences of non-compliance?",
    "Who should I contact for more information?",
  ],
  financial: [
    "What fees or charges apply to me?",
    "What are the repayment terms?",
    "Are there any penalty interest clauses?",
    "What are my rights if I want to exit this agreement?",
  ],
  other: [
    "Can you summarise the key points?",
    "What do I need to do next?",
    "Are there any important dates or deadlines?",
    "What are the most important sections?",
  ],
};

interface SuggestedQuestionsProps {
  category: DocCategory;
  onSelect: (question: string) => void;
}

export function SuggestedQuestions({ category, onSelect }: SuggestedQuestionsProps) {
  const questions = SUGGESTIONS[category] ?? SUGGESTIONS.other;

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-muted-foreground">Suggested questions</p>
      <div className="grid gap-2 sm:grid-cols-2">
        {questions.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => onSelect(q)}
            className="rounded-lg border border-border bg-muted/40 px-4 py-3 text-left text-sm transition-colors hover:border-blue-300 hover:bg-blue-50 dark:hover:bg-blue-950/20"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
