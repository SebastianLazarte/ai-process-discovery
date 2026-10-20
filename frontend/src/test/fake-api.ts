// A fake API for component tests: answers by "METHOD /path" (without /api) and records calls.
import { vi } from "vitest";

import { processSummary } from "./fixtures";

/**
 * One answer. `body` goes out as JSON; `text` as a plain or HTML page (an Nginx 504, a
 * Markdown file) with its `contentType`. `delay` holds the answer back for that many
 * milliseconds, to see a pending state.
 */
export type Reply = {
  status?: number;
  body?: unknown;
  text?: string;
  contentType?: string;
  delay?: number;
};
type Handler = Reply | ((request: Request) => Reply | Promise<Reply>);

function respond({ status = 200, body, text, contentType }: Reply): Response {
  if (status === 204) return new Response(null, { status });
  if (text !== undefined)
    return new Response(text, {
      status,
      headers: { "Content-Type": contentType ?? "text/plain; charset=utf-8" },
    });
  return Response.json(body, { status });
}

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
      if (reply.delay) await new Promise((resolve) => setTimeout(resolve, reply.delay));
      return respond(reply);
    }),
  );
  return calls;
}

/** A process as the list returns it. Kept for the tests written before fixtures.ts. */
export function summary(overrides: Partial<Record<string, unknown>> = {}) {
  return { ...processSummary(), ...overrides };
}
