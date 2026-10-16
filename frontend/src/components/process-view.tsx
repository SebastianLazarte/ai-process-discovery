"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError } from "@/lib/api";
import { useDeleteProcess, useProcess } from "@/lib/api/queries";
import { count, money, steps, version } from "@/lib/format";

import { Breadcrumbs } from "./breadcrumbs";
import { buttonClass } from "./button";
import { useToast } from "./toast";

// The page a process opens on. RS-74 turns it into the step editor; for now it shows the
// process and lets you delete it.
export function ProcessView({ id }: { id: string }) {
  const process = useProcess(id);

  if (process.isPending) return <p className="text-gray-600">Loading the process…</p>;
  if (process.isError) {
    const missing = process.error instanceof ApiError && process.error.status === 404;
    return (
      <>
        <Breadcrumbs items={[{ label: "Processes", href: "/" }, { label: "Not found" }]} />
        <h1 className="mt-4 text-2xl font-semibold">
          {missing ? "This process does not exist" : "The process could not be loaded"}
        </h1>
        <p className="mt-2 text-gray-700">
          {missing ? "It may have been deleted. Public demo data is deleted daily." : null}
        </p>
      </>
    );
  }

  const data = process.data;
  return (
    <>
      <Breadcrumbs items={[{ label: "Processes", href: "/" }, { label: data.name }]} />
      <h1 className="mt-4 text-2xl font-semibold">{data.name}</h1>
      {data.description && <p className="mt-2 max-w-2xl text-gray-700">{data.description}</p>}
      <dl className="mt-6 grid max-w-2xl grid-cols-2 gap-4 sm:grid-cols-4">
        <Fact term="Executions / month" value={count(data.executions_per_month)} />
        <Fact term="Hourly cost" value={money(data.hourly_cost)} />
        <Fact term="Steps" value={steps(data.steps.length)} />
        <Fact term="Version" value={version(data.version)} />
      </dl>
      <p className="mt-8 text-gray-700">
        The step editor arrives with the next release of this client.
      </p>
      <DeleteProcess id={data.id} name={data.name} />
    </>
  );
}

function Fact({ term, value }: { term: string; value: string }) {
  return (
    <div>
      <dt className="text-sm text-gray-600">{term}</dt>
      <dd className="font-medium tabular-nums">{value}</dd>
    </div>
  );
}

// Two steps instead of a browser confirm(): the second button names what goes, and focus
// stays in the page.
function DeleteProcess({ id, name }: { id: string; name: string }) {
  const [confirming, setConfirming] = useState(false);
  const remove = useDeleteProcess();
  const router = useRouter();
  const toast = useToast();

  if (!confirming) {
    return (
      <div className="mt-10">
        <button type="button" className={buttonClass("danger")} onClick={() => setConfirming(true)}>
          Delete process
        </button>
      </div>
    );
  }
  return (
    <div
      role="group"
      aria-labelledby="delete-title"
      className="mt-10 max-w-xl rounded-lg border border-red-700 p-4"
    >
      <p id="delete-title" className="font-medium">
        Delete “{name}” and all its analyses? This cannot be undone.
      </p>
      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          className={buttonClass("danger")}
          disabled={remove.isPending}
          onClick={() =>
            remove.mutate(id, {
              onSuccess: () => {
                toast(`Deleted “${name}”.`);
                router.push("/");
              },
            })
          }
        >
          {remove.isPending ? "Deleting…" : "Delete for good"}
        </button>
        <button
          type="button"
          className={buttonClass("secondary")}
          onClick={() => setConfirming(false)}
        >
          Keep it
        </button>
      </div>
    </div>
  );
}
