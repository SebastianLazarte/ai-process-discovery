"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { QueryClient } from "@tanstack/react-query";

import { API_PREFIX, api, unwrap } from "./client";
import type { components } from "./schema";

type Schemas = components["schemas"];
export type ProcessCreate = Schemas["ProcessCreate"];
export type ProcessUpdate = Schemas["ProcessUpdate"];
export type ProcessRead = Schemas["ProcessRead"];
export type StepCreate = Schemas["StepCreate"];
export type StepUpdate = Schemas["StepUpdate"];
export type AnalysisCreate = Schemas["AnalysisCreate"];
export type AnalysisRead = Schemas["AnalysisRead"];
export type OverrideCreate = Schemas["OverrideCreate"];

// A process owns its analysis list; an analysis owns its blueprint. Invalidations that must
// not reach the children pass exact: true.
export const keys = {
  meta: ["meta"] as const,
  demos: ["demos"] as const,
  processes: ["processes"] as const,
  process: (id: string) => ["processes", id] as const,
  analyses: (processId: string) => ["processes", processId, "analyses"] as const,
  analysis: (id: string) => ["analyses", id] as const,
  blueprint: (id: string) => ["analyses", id, "blueprint"] as const,
};

const processPath = (id: string) => ({ params: { path: { process_id: id } } });
const stepPath = (id: string) => ({ params: { path: { step_id: id } } });
const analysisPath = (id: string) => ({ params: { path: { analysis_id: id } } });

export function useMeta() {
  return useQuery({ queryKey: keys.meta, queryFn: () => unwrap(api.GET("/meta")) });
}

export function useDemos() {
  return useQuery({ queryKey: keys.demos, queryFn: () => unwrap(api.GET("/demo-processes")) });
}

export function useProcesses() {
  return useQuery({ queryKey: keys.processes, queryFn: () => unwrap(api.GET("/processes")) });
}

export function useProcess(id: string) {
  return useQuery({
    queryKey: keys.process(id),
    queryFn: () => unwrap(api.GET("/processes/{process_id}", processPath(id))),
  });
}

export function useLoadDemo() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (slug: string) =>
      unwrap(api.POST("/demo-processes/{slug}", { params: { path: { slug } } })),
    onSuccess: () => client.invalidateQueries({ queryKey: keys.processes }),
  });
}

export function useCreateProcess() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: ProcessCreate) => unwrap(api.POST("/processes", { body })),
    onSuccess: () => client.invalidateQueries({ queryKey: keys.processes }),
  });
}

export function useDeleteProcess() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => unwrap(api.DELETE("/processes/{process_id}", processPath(id))),
    onSuccess: (_, id) => {
      client.removeQueries({ queryKey: keys.process(id) });
      return client.invalidateQueries({ queryKey: keys.processes, exact: true });
    },
  });
}

// Every process and step write answers with the whole process: it replaces the cached one,
// and the list refetches for its step count, version and order.
function storeProcess(client: QueryClient, process: ProcessRead) {
  client.setQueryData(keys.process(process.id), process);
  return client.invalidateQueries({ queryKey: keys.processes, exact: true });
}

export function useUpdateProcess(id: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: ProcessUpdate) =>
      unwrap(api.PATCH("/processes/{process_id}", { ...processPath(id), body })),
    onSuccess: (process) => storeProcess(client, process),
  });
}

export function useAddStep(processId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: StepCreate) =>
      unwrap(api.POST("/processes/{process_id}/steps", { ...processPath(processId), body })),
    onSuccess: (process) => storeProcess(client, process),
  });
}

export function useUpdateStep() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ stepId, body }: { stepId: string; body: StepUpdate }) =>
      unwrap(api.PATCH("/steps/{step_id}", { ...stepPath(stepId), body })),
    onSuccess: (process) => storeProcess(client, process),
  });
}

export function useDeleteStep() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (stepId: string) => unwrap(api.DELETE("/steps/{step_id}", stepPath(stepId))),
    onSuccess: (process) => storeProcess(client, process),
  });
}

/**
 * Shows the new order at once and puts the old one back if the API refuses it. Positions
 * follow the order of the list; the API answers with the ones it stored.
 */
export function useReorderSteps(processId: string) {
  const client = useQueryClient();
  const key = keys.process(processId);
  return useMutation({
    mutationFn: (stepIds: string[]) =>
      unwrap(
        api.PUT("/processes/{process_id}/steps/order", {
          ...processPath(processId),
          body: { step_ids: stepIds },
        }),
      ),
    onMutate: async (stepIds) => {
      await client.cancelQueries({ queryKey: key, exact: true });
      const previous = client.getQueryData<ProcessRead>(key);
      if (previous) {
        const byId = new Map(previous.steps.map((step) => [step.id, step]));
        const steps = stepIds.flatMap((id, index) => {
          const step = byId.get(id);
          return step ? [{ ...step, position: index + 1 }] : [];
        });
        client.setQueryData<ProcessRead>(key, { ...previous, steps });
      }
      return { previous };
    },
    onError: (_error, _stepIds, context) => {
      if (context?.previous) client.setQueryData(key, context.previous);
    },
    onSuccess: (process) => storeProcess(client, process),
  });
}

export function useAnalyses(processId: string) {
  return useQuery({
    queryKey: keys.analyses(processId),
    queryFn: () => unwrap(api.GET("/processes/{process_id}/analyses", processPath(processId))),
  });
}

export function useAnalysis(id: string) {
  return useQuery({
    queryKey: keys.analysis(id),
    queryFn: () => unwrap(api.GET("/analyses/{analysis_id}", analysisPath(id))),
  });
}

/** Never retried: a second POST would run, and with the LLM pay for, a second analysis. */
export function useRunAnalysis(processId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: AnalysisCreate) =>
      unwrap(api.POST("/processes/{process_id}/analyses", { ...processPath(processId), body })),
    retry: false,
    onSuccess: (analysis) => {
      client.setQueryData(keys.analysis(analysis.id), analysis);
      return client.invalidateQueries({ queryKey: keys.analyses(processId) });
    },
  });
}

/** An override changes the analysis, its row in the history and its blueprint. */
export function useAddOverride(analysisId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: OverrideCreate) =>
      unwrap(api.POST("/analyses/{analysis_id}/overrides", { ...analysisPath(analysisId), body })),
    onSuccess: (analysis) => {
      client.setQueryData(keys.analysis(analysis.id), analysis);
      return Promise.all([
        client.invalidateQueries({ queryKey: keys.analyses(analysis.process_id) }),
        client.invalidateQueries({ queryKey: keys.blueprint(analysis.id) }),
      ]);
    },
  });
}

export function useBlueprint(analysisId: string) {
  return useQuery({
    queryKey: keys.blueprint(analysisId),
    queryFn: () => unwrap(api.GET("/analyses/{analysis_id}/blueprint", analysisPath(analysisId))),
  });
}

/**
 * The same-origin address of the blueprint as Markdown, for a plain download link. The
 * browser fetches it, so no client code reads the file.
 */
export function blueprintMarkdownUrl(analysisId: string): string {
  return `${API_PREFIX}/analyses/${encodeURIComponent(analysisId)}/blueprint.md`;
}
