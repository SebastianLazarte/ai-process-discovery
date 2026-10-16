import { describe, expect, it } from "vitest";

import { toApiError } from "./errors";

describe("toApiError", () => {
  it("maps request validation to one message per field, without the body prefix", () => {
    const error = toApiError(422, {
      detail: [
        { loc: ["body", "name"], msg: "Field required" },
        { loc: ["body", "steps", 0, "minutes_per_execution"], msg: "Must be positive" },
      ],
    });
    expect(error.message).toBe("Check the highlighted fields.");
    expect(error.fields).toEqual({
      name: "Field required",
      "steps.0.minutes_per_execution": "Must be positive",
    });
    expect(error.isFieldError).toBe(true);
  });

  it("maps a domain validation error to its field", () => {
    const error = toApiError(422, {
      detail: "Occurrence rate must be between 0 and 1.",
      field: "occurrence_rate",
      code: "domain_validation",
    });
    expect(error.fields).toEqual({ occurrence_rate: "Occurrence rate must be between 0 and 1." });
  });

  it("keeps the detail of any other error as its message, with no fields", () => {
    const error = toApiError(409, {
      detail: "Confirm the sensitive steps first.",
      code: "conflict",
    });
    expect(error.message).toBe("Confirm the sensitive steps first.");
    expect(error.isFieldError).toBe(false);
  });

  it("falls back to the status when the body says nothing", () => {
    expect(toApiError(502, undefined).message).toBe("Request failed (502).");
  });
});
