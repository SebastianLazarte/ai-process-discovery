import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

// Hard rule 7 and ADR 0009: one module talks to the API, and no component injects raw HTML.
const FETCH = "Only src/lib/api/ may call fetch (hard rule 7). Use the typed API client.";
const RAW_HTML =
  "dangerouslySetInnerHTML is forbidden in frontend/ (hard rule 7). Render text through React.";

export default defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      "no-restricted-globals": ["error", { name: "fetch", message: FETCH }],
      "no-restricted-properties": [
        "error",
        { object: "window", property: "fetch", message: FETCH },
        { object: "globalThis", property: "fetch", message: FETCH },
        { object: "self", property: "fetch", message: FETCH },
      ],
      "react/no-danger": "error",
      // react/no-danger only sees the JSX attribute; this also catches props built as objects.
      "no-restricted-syntax": [
        "error",
        { selector: "JSXAttribute[name.name='dangerouslySetInnerHTML']", message: RAW_HTML },
        { selector: "Property[key.name='dangerouslySetInnerHTML']", message: RAW_HTML },
      ],
    },
  },
  {
    files: ["src/lib/api/**"],
    rules: { "no-restricted-globals": "off", "no-restricted-properties": "off" },
  },
  globalIgnores([".next/**", "coverage/**", "next-env.d.ts", "src/lib/api/schema.d.ts"]),
]);
