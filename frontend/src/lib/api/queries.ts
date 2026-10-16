"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "./client";
import type { components } from "./schema";

export type ProcessCreate = components["schemas"]["ProcessCreate"];

const keys = {
  meta: ["meta"] as const,
  demos: ["demos"] as const,
  processes: ["processes"] as const,
  process: (id: string) => ["processes", id] as const,
};

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
    queryFn: () =>
      unwrap(api.GET("/processes/{process_id}", { params: { path: { process_id: id } } })),
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
    mutationFn: (id: string) =>
      unwrap(api.DELETE("/processes/{process_id}", { params: { path: { process_id: id } } })),
    onSuccess: (_, id) => {
      client.removeQueries({ queryKey: keys.process(id) });
      return client.invalidateQueries({ queryKey: keys.processes, exact: true });
    },
  });
}
