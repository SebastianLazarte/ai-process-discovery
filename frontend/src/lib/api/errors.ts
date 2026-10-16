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

type ValidationItem = { loc?: (string | number)[]; msg?: string };

// Three shapes reach the client: request validation ({detail: [{loc, msg}]}), domain
// validation ({detail, field}) and every other error ({detail, code}).
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
  const message =
    typeof detail === "string" && detail
      ? detail
      : typeof body === "string" && body
        ? body
        : `Request failed (${status}).`;
  const field = (body as { field?: unknown } | null)?.field;
  return new ApiError(status, message, typeof field === "string" ? { [field]: message } : {});
}
