import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  test: {
    // Worker threads start much faster than forked processes, which on Windows timed out
    // while jsdom and ESLint loaded side by side.
    pool: "threads",
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
