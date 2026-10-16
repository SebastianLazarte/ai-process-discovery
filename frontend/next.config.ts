import type { NextConfig } from "next";

// ADR 0009: a standalone server under /app while the vanilla client still owns /ui/.
// In development the API runs on :8000; in production Nginx routes /api/ to FastAPI.
const config: NextConfig = {
  output: "standalone",
  basePath: "/app",
  poweredByHeader: false,
  // The dev badge sat over the sidebar foot.
  devIndicators: { position: "bottom-right" },
  async rewrites() {
    if (process.env.NODE_ENV !== "development") return [];
    return [
      { source: "/api/:path*", destination: "http://localhost:8000/api/:path*", basePath: false },
    ];
  },
};

export default config;
