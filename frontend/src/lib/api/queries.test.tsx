// The query hooks against the fake API: the path and body of each call, and which cached
// data each write replaces or refetches.
import { act, cleanup, renderHook, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Providers } from "@/app/providers";
import { fakeApi } from "@/test/fake-api";
import {
  ANALYSIS_ID,
  PROCESS_ID,
  analysisRead,
  analysisSummary,
  blueprint,
  processRead,
  processSummary,
  step,
  stepFields,
} from "@/test/fixtures";

import {
  blueprintMarkdownUrl,
  useAddOverride,
  useAddStep,
  useAnalyses,
  useAnalysis,
  useBlueprint,
  useDeleteStep,
  useProcess,
  useProcesses,
  useReorderSteps,
  useRunAnalysis,
  useUpdateProcess,
  useUpdateStep,
} from "./queries";

const wrapper = ({ children }: { children: ReactNode }) => <Providers>{children}</Providers>;

const PROCESS = `/processes/${PROCESS_ID}`;
const FIRST = step({ id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", position: 1, name: "First" });
const SECOND = step({ id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", position: 2, name: "Second" });
const STORED = processRead({ steps: [FIRST, SECOND] });

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const count = (calls: string[], key: string) => calls.filter((call) => call === key).length;

/** The process and the list on screen, as every process page has them. */
function withProcess<T>(write: () => T) {
  return renderHook(
    () => ({ list: useProcesses(), process: useProcess(PROCESS_ID), write: write() }),
    {
      wrapper,
    },
  );
}

describe("process and step writes", () => {
  it("useUpdateProcess sends the changes and stores the process it gets back", async () => {
    let sent: unknown;
    const updated = processRead({ name: "Renamed", version: 2 });
    const calls = fakeApi({
      "GET /processes": { body: [processSummary()] },
      [`GET ${PROCESS}`]: { body: STORED },
      [`PATCH ${PROCESS}`]: async (request) => {
        sent = await request.json();
        return { body: updated };
      },
    });
    const { result } = withProcess(() => useUpdateProcess(PROCESS_ID));
    await waitFor(() => expect(result.current.process.isSuccess).toBe(true));

    await act(() => result.current.write.mutateAsync({ name: "Renamed" }));

    expect(sent).toEqual({ name: "Renamed" });
    await waitFor(() => expect(result.current.process.data?.name).toBe("Renamed"));
    await waitFor(() => expect(count(calls, "GET /processes")).toBe(2));
    expect(count(calls, `GET ${PROCESS}`)).toBe(1);
  });

  it("useAddStep posts to the process and stores the process it gets back", async () => {
    const calls = fakeApi({
      "GET /processes": { body: [processSummary()] },
      [`GET ${PROCESS}`]: { body: processRead({ steps: [FIRST] }) },
      [`POST ${PROCESS}/steps`]: { status: 201, body: STORED },
    });
    const { result } = withProcess(() => useAddStep(PROCESS_ID));
    await waitFor(() => expect(result.current.process.isSuccess).toBe(true));

    await act(() => result.current.write.mutateAsync(stepFields({ name: "Second" })));

    await waitFor(() =>
      expect(result.current.process.data?.steps.map((s) => s.name)).toEqual(["First", "Second"]),
    );
    await waitFor(() => expect(count(calls, "GET /processes")).toBe(2));
  });

  it("useUpdateStep patches the step and stores the process it gets back", async () => {
    let sent: unknown;
    const calls = fakeApi({
      "GET /processes": { body: [processSummary()] },
      [`GET ${PROCESS}`]: { body: STORED },
      [`PATCH /steps/${FIRST.id}`]: async (request) => {
        sent = await request.json();
        return { body: processRead({ steps: [{ ...FIRST, name: "Renamed" }, SECOND] }) };
      },
    });
    const { result } = withProcess(() => useUpdateStep());
    await waitFor(() => expect(result.current.process.isSuccess).toBe(true));

    await act(() =>
      result.current.write.mutateAsync({ stepId: FIRST.id, body: { name: "Renamed" } }),
    );

    expect(sent).toEqual({ name: "Renamed" });
    await waitFor(() => expect(result.current.process.data?.steps[0]?.name).toBe("Renamed"));
    await waitFor(() => expect(count(calls, "GET /processes")).toBe(2));
  });

  it("useDeleteStep deletes the step and stores the process it gets back", async () => {
    const calls = fakeApi({
      "GET /processes": { body: [processSummary()] },
      [`GET ${PROCESS}`]: { body: STORED },
      [`DELETE /steps/${FIRST.id}`]: { body: processRead({ steps: [{ ...SECOND, position: 1 }] }) },
    });
    const { result } = withProcess(() => useDeleteStep());
    await waitFor(() => expect(result.current.process.isSuccess).toBe(true));

    await act(() => result.current.write.mutateAsync(FIRST.id));

    await waitFor(() =>
      expect(result.current.process.data?.steps.map((s) => s.name)).toEqual(["Second"]),
    );
    await waitFor(() => expect(count(calls, "GET /processes")).toBe(2));
  });
});

describe("useReorderSteps", () => {
  const reordered = processRead({
    steps: [
      { ...SECOND, position: 1 },
      { ...FIRST, position: 2 },
    ],
  });

  it("shows the new order before the API answers", async () => {
    let sent: unknown;
    fakeApi({
      "GET /processes": { body: [processSummary()] },
      [`GET ${PROCESS}`]: { body: STORED },
      [`PUT ${PROCESS}/steps/order`]: async (request) => {
        sent = await request.json();
        return { body: reordered, delay: 50 };
      },
    });
    const { result } = withProcess(() => useReorderSteps(PROCESS_ID));
    await waitFor(() => expect(result.current.process.isSuccess).toBe(true));

    act(() => result.current.write.mutate([SECOND.id, FIRST.id]));

    await waitFor(() =>
      expect(result.current.process.data?.steps.map((s) => [s.name, s.position])).toEqual([
        ["Second", 1],
        ["First", 2],
      ]),
    );
    expect(result.current.write.isPending).toBe(true);
    await waitFor(() => expect(result.current.write.isSuccess).toBe(true));
    expect(sent).toEqual({ step_ids: [SECOND.id, FIRST.id] });
    expect(result.current.process.data).toEqual(reordered);
  });

  it("puts the old order back when the API refuses the new one", async () => {
    fakeApi({
      "GET /processes": { body: [processSummary()] },
      [`GET ${PROCESS}`]: { body: STORED },
      [`PUT ${PROCESS}/steps/order`]: {
        status: 422,
        body: { detail: "List every step of the process once." },
        delay: 20,
      },
    });
    const { result } = withProcess(() => useReorderSteps(PROCESS_ID));
    await waitFor(() => expect(result.current.process.isSuccess).toBe(true));

    act(() => result.current.write.mutate([SECOND.id, FIRST.id]));
    await waitFor(() => expect(result.current.process.data?.steps[0]?.name).toBe("Second"));

    await waitFor(() => expect(result.current.write.isError).toBe(true));
    expect(result.current.process.data?.steps.map((s) => s.name)).toEqual(["First", "Second"]);
    expect(screen.getByRole("status").textContent).toBe("List every step of the process once.");
  });
});

describe("analyses", () => {
  it("useAnalyses, useAnalysis and useBlueprint read their own paths", async () => {
    const calls = fakeApi({
      [`GET ${PROCESS}/analyses`]: { body: [analysisSummary()] },
      [`GET /analyses/${ANALYSIS_ID}`]: { body: analysisRead() },
      [`GET /analyses/${ANALYSIS_ID}/blueprint`]: { body: blueprint() },
    });
    const { result } = renderHook(
      () => ({
        list: useAnalyses(PROCESS_ID),
        analysis: useAnalysis(ANALYSIS_ID),
        blueprint: useBlueprint(ANALYSIS_ID),
      }),
      { wrapper },
    );

    await waitFor(() => expect(result.current.blueprint.isSuccess).toBe(true));
    await waitFor(() => expect(result.current.analysis.isSuccess).toBe(true));
    await waitFor(() => expect(result.current.list.isSuccess).toBe(true));
    expect(result.current.list.data?.[0]?.id).toBe(ANALYSIS_ID);
    expect(result.current.analysis.data?.rules_version).toBe("1.0.0");
    expect(result.current.blueprint.data?.automation_opportunities).toHaveLength(1);
    expect(calls).toHaveLength(3);
  });

  it("useRunAnalysis posts once, never retries, and refreshes the history", async () => {
    let reply = { status: 504, text: "<html><title>504 Gateway Time-out</title></html>" } as {
      status?: number;
      text?: string;
      body?: unknown;
    };
    const calls = fakeApi({
      [`GET ${PROCESS}/analyses`]: { body: [] },
      [`POST ${PROCESS}/analyses`]: () => reply,
    });
    const { result } = renderHook(
      () => ({ list: useAnalyses(PROCESS_ID), run: useRunAnalysis(PROCESS_ID) }),
      { wrapper },
    );
    await waitFor(() => expect(result.current.list.isSuccess).toBe(true));

    await act(() =>
      result.current.run
        .mutateAsync({ use_llm: true, confirm_sensitive: false })
        .catch(() => undefined),
    );
    expect(count(calls, `POST ${PROCESS}/analyses`)).toBe(1);
    await waitFor(() =>
      expect(result.current.run.error?.message).toBe(
        "The API took too long to answer. Try again in a moment.",
      ),
    );

    reply = { status: 201, body: analysisRead() };
    await act(() => result.current.run.mutateAsync({ use_llm: false, confirm_sensitive: false }));
    await waitFor(() => expect(count(calls, `GET ${PROCESS}/analyses`)).toBe(2));
  });

  it("useAddOverride stores the analysis and refreshes the history and the blueprint", async () => {
    let sent: unknown;
    const overridden = analysisRead();
    const calls = fakeApi({
      [`GET ${PROCESS}/analyses`]: { body: [analysisSummary()] },
      [`GET /analyses/${ANALYSIS_ID}`]: { body: analysisRead() },
      [`GET /analyses/${ANALYSIS_ID}/blueprint`]: { body: blueprint() },
      [`POST /analyses/${ANALYSIS_ID}/overrides`]: async (request) => {
        sent = await request.json();
        return { status: 201, body: { ...overridden, rules_version: "overridden" } };
      },
    });
    const { result } = renderHook(
      () => ({
        list: useAnalyses(PROCESS_ID),
        analysis: useAnalysis(ANALYSIS_ID),
        blueprint: useBlueprint(ANALYSIS_ID),
        override: useAddOverride(ANALYSIS_ID),
      }),
      { wrapper },
    );
    await waitFor(() => expect(result.current.blueprint.isSuccess).toBe(true));
    await waitFor(() => expect(result.current.list.isSuccess).toBe(true));
    await waitFor(() => expect(result.current.analysis.isSuccess).toBe(true));

    const body = { step_id: FIRST.id, human_control: "REQUIRED", reason: "Legal asks" } as const;
    await act(() => result.current.override.mutateAsync(body));

    expect(sent).toEqual(body);
    await waitFor(() => expect(result.current.analysis.data?.rules_version).toBe("overridden"));
    await waitFor(() => expect(count(calls, `GET /analyses/${ANALYSIS_ID}/blueprint`)).toBe(2));
    await waitFor(() => expect(count(calls, `GET ${PROCESS}/analyses`)).toBe(2));
    expect(count(calls, `GET /analyses/${ANALYSIS_ID}`)).toBe(1);
  });
});

describe("blueprintMarkdownUrl", () => {
  it("points at the Markdown on the same origin", () => {
    expect(blueprintMarkdownUrl(ANALYSIS_ID)).toBe(`/api/analyses/${ANALYSIS_ID}/blueprint.md`);
  });
});
