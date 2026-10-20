// RS-75: the Analyse form with assumptions and an honest wait for the LLM.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GATEWAY_MESSAGES } from "@/lib/api";
import { fakeApi } from "@/test/fake-api";
import type { Reply } from "@/test/fake-api";
import { ANALYSIS_ID, analysisRead, processRead, step } from "@/test/fixtures";
import { push, renderWithProviders } from "@/test/render";

import { AnalyseView } from "./analyse-view";
import { LlmUnavailableNote, START_MESSAGE } from "./llm-wait";

vi.mock("next/navigation", async () => ({ useRouter: () => ({ push }) }));

const SENSITIVE_ID = "77777777-7777-4777-8777-777777777777";
const PROCESS = processRead({
  steps: [
    step(),
    step({
      id: SENSITIVE_ID,
      position: 2,
      name: "Check the customer record",
      handles_sensitive_data: true,
    }),
  ],
});
const PATH = `/processes/${PROCESS.id}`;
const RUN = `POST ${PATH}/analyses`;
const RESULTS = `${PATH}/analyses/${ANALYSIS_ID}`;

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  push.mockReset();
});

type RunHandler = Reply | ((request: Request) => Promise<Reply>);

/** A list of replies answers successive runs in order. */
function api(run: RunHandler | Reply[]) {
  const replies = Array.isArray(run) ? [...run] : null;
  const handler: RunHandler = replies
    ? async () => replies.shift() ?? { status: 500 }
    : (run as RunHandler);
  return fakeApi({
    [`GET ${PATH}`]: { body: PROCESS },
    [`GET ${PATH}/analyses`]: { body: [] },
    [RUN]: handler,
  });
}

const runButton = () => screen.getByRole("button", { name: "Run analysis" });
const llmToggle = () =>
  screen.getByRole("checkbox", { name: /Enrich with the LLM/ }) as HTMLInputElement;

describe("the sensitive-data confirmation", () => {
  it("keeps Run analysis disabled with the LLM on until the notice is confirmed", async () => {
    api({ status: 201, body: analysisRead() });
    renderWithProviders(<AnalyseView id={PROCESS.id} />);

    await screen.findByRole("heading", { name: "Analyse" });
    expect((runButton() as HTMLButtonElement).disabled).toBe(false);

    fireEvent.click(llmToggle());
    expect(screen.getByText(/Check the customer record/, { selector: "p" })).toBeDefined();
    expect((runButton() as HTMLButtonElement).disabled).toBe(true);

    fireEvent.click(
      screen.getByRole("checkbox", {
        name: "I confirm these descriptions can be sent to the provider",
      }),
    );
    expect((runButton() as HTMLButtonElement).disabled).toBe(false);
  });

  it("shows a 409 as a notice and reloads the process", async () => {
    const detail =
      "these steps handle sensitive data and would be sent to the LLM provider: Check the customer record.";
    const calls = api({ status: 409, body: { detail, code: "conflict" } });
    renderWithProviders(<AnalyseView id={PROCESS.id} />);

    fireEvent.click(await screen.findByRole("button", { name: "Run analysis" }));

    expect(await screen.findByText(`The analysis did not run: ${detail}`)).toBeDefined();
    await vi.waitFor(() => expect(calls.filter((call) => call === `GET ${PATH}`)).toHaveLength(2));
  });
});

describe("a run with the LLM", () => {
  it("shows an indicator, the elapsed time and the expected wait, and announces sparingly", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    api({ status: 201, body: analysisRead(), delay: 100_000 });
    renderWithProviders(<AnalyseView id={PROCESS.id} />);

    await screen.findByRole("heading", { name: "Analyse" });
    fireEvent.click(llmToggle());
    fireEvent.click(
      screen.getByRole("checkbox", {
        name: "I confirm these descriptions can be sent to the provider",
      }),
    );
    fireEvent.click(runButton());

    expect(await screen.findByRole("progressbar", { name: "Running the analysis" })).toBeDefined();
    expect(screen.getByText(/expected wait up to 3 min/)).toBeDefined();
    expect(screen.getByRole("timer").textContent).toBe("0:00");
    expect(screen.getByRole("link", { name: "History" }).getAttribute("href")).toBe(
      `${PATH}/history`,
    );
    expect(screen.getByText(/Leaving this page does not cancel the run/)).toBeDefined();
    const region = screen.getByText(START_MESSAGE);
    expect(region.getAttribute("aria-live")).toBe("polite");
    expect((screen.getByRole("button", { name: "Running…" }) as HTMLButtonElement).disabled).toBe(
      true,
    );

    await act(() => vi.advanceTimersByTimeAsync(20_000));
    expect(screen.getByRole("timer").textContent).toBe("0:20");
    expect(region.textContent).toBe(START_MESSAGE);

    await act(() => vi.advanceTimersByTimeAsync(10_000));
    expect(region.textContent).toBe("Still running: 30 seconds elapsed.");

    await act(() => vi.advanceTimersByTimeAsync(25_000));
    expect(screen.getByRole("timer").textContent).toBe("0:55");
    expect(region.textContent).toBe("Still running: 30 seconds elapsed.");

    await act(() => vi.advanceTimersByTimeAsync(5_000));
    expect(region.textContent).toBe("Still running: 1 min elapsed.");

    await act(() => vi.advanceTimersByTimeAsync(41_000));
    await vi.waitFor(() => expect(push).toHaveBeenCalledWith(RESULTS));
    expect(screen.getByText("Analysis saved.")).toBeDefined();
  });

  it("sends one run for a double click", async () => {
    const calls = api({ status: 201, body: analysisRead(), delay: 50 });
    renderWithProviders(<AnalyseView id={PROCESS.id} />);

    const button = await screen.findByRole("button", { name: "Run analysis" });
    fireEvent.click(button);
    fireEvent.click(button);

    await vi.waitFor(() => expect(push).toHaveBeenCalledWith(RESULTS));
    expect(calls.filter((call) => call === RUN)).toHaveLength(1);
  });

  it("sends the assumptions as typed, and only the reductions that were set", async () => {
    let body: unknown;
    api(async (request) => {
      body = await request.json();
      return { status: 201, body: analysisRead() };
    });
    renderWithProviders(<AnalyseView id={PROCESS.id} />);

    fireEvent.change(await screen.findByRole("textbox", { name: "Implementation cost" }), {
      target: { value: "25000" },
    });
    fireEvent.change(screen.getByRole("slider", { name: "2. Check the customer record" }), {
      target: { value: "0.35" },
    });
    expect(screen.getByText("35%")).toBeDefined();
    fireEvent.click(runButton());

    await vi.waitFor(() => expect(push).toHaveBeenCalledWith(RESULTS));
    expect(body).toEqual({
      use_llm: false,
      confirm_sensitive: false,
      assumptions: {
        implementation_cost: "25000",
        monthly_tooling_cost: "0",
        expected_time_reduction_by_step: { [SENSITIVE_ID]: "0.35" },
      },
    });
  });
});

describe("a failed run", () => {
  it("keeps every value and offers a retry, after a 504 that Nginx sends as HTML", async () => {
    const calls = api([
      {
        status: 504,
        text: "<html><body>504 Gateway Time-out</body></html>",
        contentType: "text/html",
      },
      { status: 201, body: analysisRead() },
    ]);
    renderWithProviders(<AnalyseView id={PROCESS.id} />);

    const cost = await screen.findByRole("textbox", { name: "Implementation cost" });
    fireEvent.change(cost, { target: { value: "25000" } });
    const slider = screen.getByRole("slider", { name: "1. Read the claim email" });
    fireEvent.change(slider, { target: { value: "0.5" } });
    fireEvent.click(runButton());

    expect(
      await screen.findByText(`The analysis did not run: ${GATEWAY_MESSAGES[504]}`),
    ).toBeDefined();
    expect(screen.getByText(/It may still finish on the server/)).toBeDefined();
    expect(screen.queryByText(/<html>/)).toBeNull();
    expect((cost as HTMLInputElement).value).toBe("25000");
    expect((slider as HTMLInputElement).value).toBe("0.5");

    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await vi.waitFor(() => expect(push).toHaveBeenCalledWith(RESULTS));
    expect(calls.filter((call) => call === RUN)).toHaveLength(2);
  });
});

describe("an analysis whose LLM hit the daily quota", () => {
  it("says the deterministic results are complete and today's AI quota is used up", () => {
    const { llm } = analysisRead({
      llm: {
        status: "unavailable",
        provider: null,
        model: null,
        prompt_version: null,
        error_kind: "daily_quota",
      },
    });
    render(<LlmUnavailableNote llm={llm} />);

    const note = screen.getByRole("note");
    expect(note.textContent).toMatch(/Today's AI quota of this demo is used up/);
    expect(note.textContent).toMatch(/The deterministic results are complete/);
  });
});
