"use client";

import { useId, useState } from "react";
import type { ReactNode } from "react";

import { buttonClass } from "./button";

type Confirmation = {
  question: ReactNode;
  confirmLabel: string;
  pendingLabel: string;
  cancelLabel?: string;
  pending?: boolean;
  onConfirm: () => void;
};

// A destructive action in two steps instead of a browser confirm(): the first button asks,
// the second names what goes, and focus stays in the page.
export function ConfirmButton({ label, ...confirmation }: Confirmation & { label: string }) {
  const [confirming, setConfirming] = useState(false);

  if (!confirming) {
    return (
      <button type="button" className={buttonClass("danger")} onClick={() => setConfirming(true)}>
        {label}
      </button>
    );
  }
  return <ConfirmQuestion {...confirmation} onCancel={() => setConfirming(false)} />;
}

/** The second step on its own, for a caller that keeps its first button in place. */
export function ConfirmQuestion({
  question,
  confirmLabel,
  pendingLabel,
  cancelLabel = "Keep it",
  pending = false,
  onConfirm,
  onCancel,
  className = "",
}: Confirmation & { onCancel: () => void; className?: string }) {
  const questionId = useId();
  return (
    <div
      role="group"
      aria-labelledby={questionId}
      className={`max-w-xl rounded-r-control border-l-[3px] border-bad bg-bad-bg px-4 py-3 ${className}`}
    >
      <p id={questionId} className="text-sm text-ink">
        {question}
      </p>
      <div className="mt-3 flex flex-wrap gap-3">
        <button
          type="button"
          className={buttonClass("danger")}
          disabled={pending}
          onClick={onConfirm}
        >
          {pending ? pendingLabel : confirmLabel}
        </button>
        <button type="button" className={buttonClass("secondary")} onClick={onCancel}>
          {cancelLabel}
        </button>
      </div>
    </div>
  );
}
