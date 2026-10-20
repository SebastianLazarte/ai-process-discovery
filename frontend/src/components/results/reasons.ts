import type { AnalysisRead } from "@/lib/api/queries";

// Why a figure is unknown, from which inputs the API left out. The rules leave a figure null
// only for these reasons (domain/business_case.py, domain/scoring.py), and the client only
// reads which ones are null: it never compares or computes a figure.

type Impact = AnalysisRead["business_impact"];

export const NO_HOURLY_COST = "Hourly cost not set";
export const NO_IMPLEMENTATION_COST = "Implementation cost not given";
export const NO_TIME = "The process takes no time, so there is nothing to weigh";

/** The reason a payback period is null: a missing input, or net savings that never repay. */
export function paybackReason(impact: Impact): string {
  if (impact.net_monthly_savings === null) return NO_HOURLY_COST;
  if (impact.implementation_cost === null) return NO_IMPLEMENTATION_COST;
  return "Net savings are not positive, so it never pays back";
}

/** The reason an ROI is null: a missing input, or no implementation cost to divide by. */
export function roiReason(impact: Impact): string {
  if (impact.net_monthly_savings === null) return NO_HOURLY_COST;
  if (impact.implementation_cost === null) return NO_IMPLEMENTATION_COST;
  return "The implementation cost is zero";
}

/** The note under a figure: its reason when the API left it null, else nothing. */
export function unknownNote(value: string | null, reason: string): string | undefined {
  return value === null ? reason : undefined;
}
