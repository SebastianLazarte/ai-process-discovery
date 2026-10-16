import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import HomePage from "./page";

afterEach(cleanup);

describe("HomePage", () => {
  it("names the product as its main heading", () => {
    render(<HomePage />);
    expect(screen.getByRole("heading", { level: 1, name: "AI Process Discovery" })).toBeDefined();
  });

  it("links to the current client, served at /ui/ outside development", () => {
    render(<HomePage />);
    const link = screen.getByRole("link", { name: "open the current client" });
    expect(link.getAttribute("href")).toBe("/ui/");
  });
});
