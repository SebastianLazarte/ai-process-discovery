"use client";

import { useEffect, useId, useRef } from "react";
import type { ReactNode } from "react";

// A modal on the native <dialog>: the browser traps focus, closes it on Escape and returns
// focus to what opened it. `open` drives it; every way of closing calls onClose.
export function Dialog({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      // jsdom has no showModal; the attribute opens it the same way for tests.
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
    } else if (!open && dialog.open) {
      if (typeof dialog.close === "function") dialog.close();
      else dialog.removeAttribute("open");
    }
  }, [open]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onClose={onClose}
      className="m-auto w-[min(560px,calc(100vw-32px))] rounded-panel border border-line bg-surface p-6 text-ink backdrop:bg-bg/70"
    >
      <h2 id={titleId} className="mb-[18px] text-[17px] leading-snug font-semibold tracking-tight">
        {title}
      </h2>
      {children}
    </dialog>
  );
}
