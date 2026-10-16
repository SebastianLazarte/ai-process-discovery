// A fake API for component tests: answers by "METHOD /path" (without /api) and records calls.
import { vi } from "vitest";

type Reply = { status?: number; body?: unknown };
type Handler = Reply | ((request: Request) => Reply | Promise<Reply>);

export function fakeApi(routes: Record<string, Handler>) {
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (request: Request) => {
      const path = new URL(request.url).pathname.replace(/^\/api/, "");
      const key = `${request.method} ${path}`;
      calls.push(key);
      const handler = routes[key];
      if (handler === undefined)
        return Response.json({ detail: `No fake for ${key}` }, { status: 500 });
      const reply = typeof handler === "function" ? await handler(request) : handler;
      const status = reply.status ?? 200;
      return status === 204
        ? new Response(null, { status })
        : Response.json(reply.body, { status });
    }),
  );
  return calls;
}

export function summary(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id: "11111111-1111-4111-8111-111111111111",
    name: "Warranty claims from installers",
    owner: "After-sales",
    executions_per_month: 180,
    step_count: 7,
    version: 1,
    updated_at: "2026-10-16T09:30:00Z",
    ...overrides,
  };
}
