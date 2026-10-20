// The only module allowed to call fetch (hard rule 7, ADR 0009). Lint enforces it.
export { api, unwrap } from "./client";
export { ApiError, GATEWAY_MESSAGES, UNREACHABLE, toApiError } from "./errors";
export { applyFieldErrors } from "./form";
export type { components, paths } from "./schema";
