// The helpers ported from web/format.js. A missing figure reads unknown, never n/a or zero.
import { describe, expect, it } from "vitest";

import {
  UNKNOWN,
  detail,
  enumLabel,
  hours,
  money,
  months,
  number,
  percent,
  score,
  shortId,
} from ".";

describe("figures", () => {
  it("print decimals as the API sends them, rounded for display only", () => {
    expect(number("1234.567")).toBe("1,234.57");
    expect(number(3, 0)).toBe("3");
    expect(hours("12.5")).toBe("12.50 h");
    expect(months("7.25")).toBe("7.3 mo");
    expect(score("71.6")).toBe("72");
  });

  it("scale a ratio to a percent", () => {
    expect(percent("0.25")).toBe("25%");
    expect(percent(0.8125, 1)).toBe("81.3%");
  });

  it.each([
    ["number", number],
    ["hours", hours],
    ["months", months],
    ["percent", percent],
    ["score", score],
    ["money", money],
  ])("%s prints a missing figure as unknown", (_, format) => {
    expect(format(null)).toBe(UNKNOWN);
    expect(format(undefined)).toBe(UNKNOWN);
    expect(format("")).toBe(UNKNOWN);
  });

  it("keep zero as zero", () => {
    expect(hours("0")).toBe("0.00 h");
    expect(percent(0)).toBe("0%");
    expect(score(0)).toBe("0");
  });
});

describe("enumLabel", () => {
  it("turns an enum into words and keeps the acronyms", () => {
    expect(enumLabel("RULE_BASED")).toBe("Rule based");
    expect(enumLabel("AI_CANDIDATE")).toBe("AI candidate");
    expect(enumLabel("API_INTEGRATION")).toBe("API integration");
    expect(enumLabel("LLM")).toBe("LLM");
    expect(enumLabel("UNKNOWN")).toBe("Unknown");
  });

  it("prints nothing for nothing", () => {
    expect(enumLabel(null)).toBe("");
    expect(enumLabel("")).toBe("");
  });
});

describe("detail", () => {
  it("labels a raw enum and lets prose through", () => {
    expect(detail("DIGITAL_STRUCTURED")).toBe("Digital structured");
    expect(detail("Inputs arrive by email")).toBe("Inputs arrive by email");
    expect(detail(3)).toBe("3");
    expect(detail(null)).toBe("");
  });
});

describe("shortId", () => {
  it("keeps the first block of a UUID", () => {
    expect(shortId("11111111-2222-4333-8444-555555555555")).toBe("11111111");
    expect(shortId(undefined)).toBe("");
  });
});
