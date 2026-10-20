// Every failed request becomes an ApiError with one message for a toast and, for a 422,
// one message per field. The same rules as describeError in web/api.js.

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly fields: Readonly<Record<string, string>> = {},
  ) {
    super(message);
    this.name = "ApiError";
  }

  /** A 422 that names fields is the form's to show, not a toast's. */
  get isFieldError(): boolean {
    return this.status === 422 && Object.keys(this.fields).length > 0;
  }
}

export const UNREACHABLE = "The API cannot be reached. Is the server running?";

// Nginx answers these itself, with an HTML page that means nothing in a toast: the rate
// limit (limit_req_status 429), an API that is down (502) or too slow (504, after the
// proxy_read_timeout of an analysis).
export const GATEWAY_MESSAGES: Readonly<Record<number, string>> = {
  429: "Too many requests in a short time. Wait a minute and try again.",
  502: "The API is not answering right now. Try again in a moment.",
  504: "The API took too long to answer. Try again in a moment.",
};

type ValidationItem = { loc?: (string | number)[]; msg?: string };

const isHtml = (text: string) => /^\s*</.test(text);

// Three shapes reach the client: request validation ({detail: [{loc, msg}]}), domain
// validation ({detail, field}) and every other error ({detail, code}). Anything else is a
// page from a proxy, shown as a sentence for its status.
export function toApiError(status: number, body: unknown): ApiError {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (Array.isArray(detail)) {
    const fields: Record<string, string> = {};
    for (const item of detail as ValidationItem[]) {
      const name = (item.loc ?? []).filter((part) => part !== "body").join(".") || "request";
      fields[name] = item.msg ?? "Invalid value.";
    }
    return new ApiError(status, "Check the highlighted fields.", fields);
  }
  const fallback = `Request failed (${status}).`;
  const message =
    typeof detail === "string" && detail
      ? detail
      : typeof body === "string" && body
        ? isHtml(body)
          ? (GATEWAY_MESSAGES[status] ?? fallback)
          : body
        : fallback;
  const field = (body as { field?: unknown } | null)?.field;
  return new ApiError(status, message, typeof field === "string" ? { [field]: message } : {});
}
