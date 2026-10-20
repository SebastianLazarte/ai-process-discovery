import type { Metadata } from "next";
import localFont from "next/font/local";
import { connection } from "next/server";
import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";

import "./globals.css";
import { Providers } from "./providers";

// Inter from its versioned package, served from this origin (ADR 0013): no font CDN at
// build time or in the browser.
const inter = localFont({
  src: "../../node_modules/@fontsource-variable/inter/files/inter-latin-wght-normal.woff2",
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI Process Discovery",
  description: "Map a process and get numbers you can defend.",
};

// The CSP nonce from src/proxy.ts exists only per request, so no page may be prerendered:
// waiting for the request renders every page dynamically, and Next stamps the nonce on
// its scripts while it renders.
export default async function RootLayout({ children }: { children: ReactNode }) {
  await connection();
  return (
    <html lang="en" className={inter.variable}>
      <body className="bg-bg font-sans text-ink antialiased">
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
