import type { components } from "@/lib/api";

import { Badge } from "../badge";

// The language of trust (docs/design/00-brief.md): who decided a step, or raised a risk,
// said in words so it never rests on colour alone. A person's decision reads "Override".

type Source = components["schemas"]["RecommendationSource"];

const LABELS: Readonly<Record<Source, string>> = {
  RULES: "Rules",
  AI: "AI",
  HUMAN: "Override",
};

export function SourceBadge({ source }: { source: Source }) {
  return <Badge value={source}>{LABELS[source] ?? source}</Badge>;
}
