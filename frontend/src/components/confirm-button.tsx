"use client";

import { useId, useState } from "react";
import type { ReactNode } from "react";

import { Button } from "./button";
import { noteClass } from "./note";

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
      <Button variant="danger" onClick={() => setConfirming(true)}>
        {label}
      </Button>
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
      className={`max-w-xl ${noteClass("bad")} ${className}`}
    >
      <p id={questionId} className="text-sm text-ink">
        {question}
      </p>
      <div className="mt-3 flex flex-wrap gap-3">
        <Button variant="danger" pending={pending} pendingLabel={pendingLabel} onClick={onConfirm}>
          {confirmLabel}
        </Button>
        <Button onClick={onCancel}>{cancelLabel}</Button>
      </div>
    </div>
  );
}
