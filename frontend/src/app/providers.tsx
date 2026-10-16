"use client";

import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import type { ReactNode } from "react";

import { ToastProvider, useToast } from "@/components/toast";
import { ApiError } from "@/lib/api";

// RS-71: a failed request shows its message in a toast, except a 422 that names fields,
// which the form shows next to each field.
function QueryProvider({ children }: { children: ReactNode }) {
  const toast = useToast();
  const [client] = useState(() => {
    const onError = (error: Error) => {
      if (error instanceof ApiError && error.isFieldError) return;
      toast(error.message, "error");
    };
    return new QueryClient({
      queryCache: new QueryCache({ onError }),
      mutationCache: new MutationCache({ onError }),
      defaultOptions: { queries: { retry: false } },
    });
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ToastProvider>
      <QueryProvider>{children}</QueryProvider>
    </ToastProvider>
  );
}
