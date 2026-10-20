// RS-93: the History tab lists the analyses newest first with their date, versions and LLM
// status, each one opens its Results, and a change of process version shows.
import { cleanup, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fakeApi } from "@/test/fake-api";
import { analysisSummary, PROCESS_ID } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";

import { HistoryView } from "./history-view";

const PATH = `GET /processes/${PROCESS_ID}/analyses`;
const NEWER = "77777777-7777-4777-8777-777777777777";
const OLDER = "88888888-8888-4888-8888-888888888888";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

/** The cells of each body row, as text, in the order the table shows them. */
async function bodyRows() {
  const table = await screen.findByRole("table", { name: "Analysis history" });
  const [, ...rows] = within(table).getAllByRole("row");
  return rows.map((row) =>
    within(row)
      .getAllByRole("cell")
      .map((cell) => cell.textContent),
  );
}

describe("the History tab", () => {
  it("lists the analyses newest first with date, versions and LLM status, each opening its Results", async () => {
    fakeApi({
      [PATH]: {
        body: [
          analysisSummary({
            id: NEWER,
            created_at: "2026-10-18T14:05:00Z",
            rules_version: "1.1.0",
            llm_status: "ok",
            override_count: 2,
          }),
          analysisSummary({ id: OLDER, created_at: "2026-10-16T10:00:00Z" }),
        ],
      },
    });
    renderWithProviders(<HistoryView id={PROCESS_ID} />);

    const [newer, older] = await bodyRows();
    expect(newer?.slice(0, 6)).toEqual([
      "2026-10-18 14:05 UTC",
      "77777777",
      "v1",
      "1.1.0",
      "Ok",
      "2",
    ]);
    expect(older?.slice(0, 6)).toEqual([
      "2026-10-16 10:00 UTC",
      "88888888",
      "v1",
      "1.0.0",
      "Not requested",
      "0",
    ]);
    expect(screen.getByRole("link", { name: "Open analysis 77777777" }).getAttribute("href")).toBe(
      `/processes/${PROCESS_ID}/analyses/${NEWER}`,
    );
    expect(screen.getByRole("link", { name: "Open analysis 88888888" }).getAttribute("href")).toBe(
      `/processes/${PROCESS_ID}/analyses/${OLDER}`,
    );
    expect(screen.getByText(/Each analysis is an immutable snapshot\./)).toBeDefined();
  });

  it("shows the change of process version between two analyses", async () => {
    fakeApi({
      [PATH]: {
        body: [
          analysisSummary({ id: NEWER, process_version: 2 }),
          analysisSummary({ id: OLDER, process_version: 1 }),
        ],
      },
    });
    renderWithProviders(<HistoryView id={PROCESS_ID} />);

    const table = await screen.findByRole("table", { name: "Analysis history" });
    const header = within(table)
      .getAllByRole("columnheader")
      .map((cell) => cell.textContent);
    const process = header.indexOf("Process");
    const versions = (await bodyRows()).map((row) => row[process]);
    expect(versions).toEqual(["v2", "v1"]);
  });

  it("says so when the process has no analyses yet", async () => {
    fakeApi({ [PATH]: { body: [] } });
    renderWithProviders(<HistoryView id={PROCESS_ID} />);

    expect(await screen.findByRole("heading", { name: "No analyses yet" })).toBeDefined();
    expect(screen.queryByRole("table")).toBeNull();
    expect(screen.getByRole("link", { name: "Analyse" }).getAttribute("href")).toBe(
      `/processes/${PROCESS_ID}/analyse`,
    );
  });
});
