import createClient from "openapi-fetch";

import { ApiError, UNREACHABLE, toApiError } from "./errors";
import type { paths } from "./schema";

// Paths in openapi.json are relative to its /api server (RS-69). In the browser that is the
// same origin: Nginx in production, the next dev rewrite in development. On the server,
// reads go straight to the API service at API_INTERNAL_URL (ADR 0009). Request needs an
// absolute URL outside the browser, so both bases are absolute.
function baseUrl(): string {
  if (typeof window !== "undefined") return `${window.location.origin}/api`;
  return `${process.env.API_INTERNAL_URL ?? "http://localhost:8000"}/api`;
}

export const api = createClient<paths>({
  baseUrl: baseUrl(),
  // Resolved on each call, so tests can stub the global.
  fetch: (request) => globalThis.fetch(request),
});

type Result<T> = { data?: T; error?: unknown; response: Response };

/** Returns the data of a call, or throws an ApiError for any failure, network included. */
export async function unwrap<T>(call: Promise<Result<T>>): Promise<T> {
  let result: Result<T>;
  try {
    result = await call;
  } catch {
    throw new ApiError(0, UNREACHABLE);
  }
  if (!result.response.ok) throw toApiError(result.response.status, result.error);
  return result.data as T;
}
