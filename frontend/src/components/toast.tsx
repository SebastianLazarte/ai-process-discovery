"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";

type Tone = "info" | "error";
type Toast = { message: string; tone: Tone };
type ShowToast = (message: string, tone?: Tone) => void;

const ToastContext = createContext<ShowToast | null>(null);

const DISMISS_MS = 6000;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<Toast | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const show = useCallback<ShowToast>((message, tone = "info") => {
    clearTimeout(timer.current);
    setToast({ message, tone });
    timer.current = setTimeout(() => setToast(null), DISMISS_MS);
  }, []);

  useEffect(() => () => clearTimeout(timer.current), []);

  return (
    <ToastContext.Provider value={show}>
      {children}
      {/* The live region exists before any message, so screen readers announce each one. */}
      <div
        role="status"
        aria-live="polite"
        className="fixed inset-x-4 bottom-4 z-50 flex justify-end md:inset-x-auto md:right-6 md:bottom-6"
      >
        {toast && (
          <p
            data-tone={toast.tone}
            className="max-w-[440px] rounded-[10px] border border-toast-line bg-toast px-5 py-3.5 text-sm text-ink shadow-xl data-[tone=error]:border-toast-error-line data-[tone=error]:bg-toast-error"
          >
            {toast.message}
          </p>
        )}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ShowToast {
  const show = useContext(ToastContext);
  if (show === null) throw new Error("useToast needs a ToastProvider");
  return show;
}
