import type { NextConfig } from "next";

// ADR 0009, ADR 0016: a standalone server at the root of the site from 2.0.0.
// In development the API runs on :8000; in production Nginx routes /api/ to FastAPI.
const config: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  // The dev badge sat over the sidebar foot.
  devIndicators: { position: "bottom-right" },
  async rewrites() {
    if (process.env.NODE_ENV !== "development") return [];
    return [{ source: "/api/:path*", destination: "http://localhost:8000/api/:path*" }];
  },
};

export default config;
