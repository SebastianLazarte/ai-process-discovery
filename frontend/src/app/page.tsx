// In production Nginx serves the vanilla client at /ui/ on the same origin (ADR 0009).
// In development nothing routes /ui/, so the link goes straight to the API server.
const CURRENT_CLIENT =
  process.env.NODE_ENV === "development" ? "http://localhost:8000/ui/" : "/ui/";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-16">
      <h1 className="text-3xl font-semibold">AI Process Discovery</h1>
      <p className="mt-4">
        The new client is under construction. Meanwhile,{" "}
        <a className="underline underline-offset-4" href={CURRENT_CLIENT}>
          open the current client
        </a>
        .
      </p>
    </main>
  );
}
