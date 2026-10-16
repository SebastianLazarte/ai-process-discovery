import { describe, expect, it } from "vitest";

import { count, money, steps, timestamp, version } from ".";

describe("format", () => {
  it("prints an unknown amount as unknown, never as zero", () => {
    expect(money(null)).toBe("unknown");
    expect(money("0")).toBe("0.00");
    expect(money("1234.5")).toBe("1,234.50");
  });

  it("prints counts, steps and versions", () => {
    expect(count(1800)).toBe("1,800");
    expect(steps(1)).toBe("1 step");
    expect(steps(7)).toBe("7 steps");
    expect(version(3)).toBe("v3");
  });

  it("prints timestamps in UTC to the minute", () => {
    expect(timestamp("2026-10-16T09:30:12.345Z")).toBe("2026-10-16 09:30 UTC");
  });
});
