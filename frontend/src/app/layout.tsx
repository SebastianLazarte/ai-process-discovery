import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "AI Process Discovery",
  description: "Map a process and get numbers you can defend.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-white text-gray-900">
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
