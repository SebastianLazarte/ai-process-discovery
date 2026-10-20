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

describe("pages that Nginx answers itself", () => {
  const page = (title: string) =>
    `<html>\r\n<head><title>${title}</title></head>\r\n<body><center><h1>${title}</h1></center></body>\r\n</html>`;

  it.each([
    [
      429,
      "429 Too Many Requests",
      "Too many requests in a short time. Wait a minute and try again.",
    ],
    [502, "502 Bad Gateway", "The API is not answering right now. Try again in a moment."],
    [504, "504 Gateway Time-out", "The API took too long to answer. Try again in a moment."],
  ])("a %s shows a sentence instead of the HTML", (status, title, message) => {
    const error = toApiError(status, page(title));
    expect(error.message).toBe(message);
    expect(error.status).toBe(status);
    expect(error.isFieldError).toBe(false);
  });

  it("falls back to the status for any other HTML page", () => {
    expect(toApiError(500, page("500 Internal Server Error")).message).toBe(
      "Request failed (500).",
    );
  });

  it("keeps a plain text body as the message", () => {
    expect(toApiError(500, "Internal Server Error").message).toBe("Internal Server Error");
  });
});
