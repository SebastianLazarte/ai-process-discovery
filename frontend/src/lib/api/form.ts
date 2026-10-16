import type { FieldValues, Path, UseFormSetError } from "react-hook-form";

import type { ApiError } from "./errors";

/**
 * Puts each field message of a 422 on the form control with the same name, so the field
 * shows its own error (RS-71). Returns the messages that matched no control, for the form
 * to show above its button.
 */
export function applyFieldErrors<T extends FieldValues>(
  error: ApiError,
  setError: UseFormSetError<T>,
  names: readonly Path<T>[],
): string[] {
  const unmatched: string[] = [];
  let first = true;
  for (const [field, message] of Object.entries(error.fields)) {
    const name = names.find((candidate) => candidate === field || field.endsWith(`.${candidate}`));
    if (name === undefined) {
      unmatched.push(`${field}: ${message}`);
      continue;
    }
    setError(name, { type: "server", message }, { shouldFocus: first });
    first = false;
  }
  return unmatched;
}
