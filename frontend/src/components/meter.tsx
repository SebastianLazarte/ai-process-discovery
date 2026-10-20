// A score on the native <meter>, as in web/views.js: the browser colours it good, warning
// or bad from low, high and optimum. No inline style, because the CSP blocks style= (RS-72).
export function Meter({
  value,
  label,
  min = 0,
  max = 100,
  low = 40,
  high = 70,
  optimum = 100,
}: {
  /** The figure the API returned; the meter only places it. */
  value: string | number;
  label: string;
  min?: number;
  max?: number;
  low?: number;
  high?: number;
  optimum?: number;
}) {
  return (
    <meter
      min={min}
      max={max}
      low={low}
      high={high}
      optimum={optimum}
      value={Number(value)}
      aria-label={label}
      className="block h-2.5 w-full [&::-moz-meter-bar]:rounded-md [&::-moz-meter-bar]:bg-good [&::-webkit-meter-bar]:h-2.5 [&::-webkit-meter-bar]:rounded-md [&::-webkit-meter-bar]:border-0 [&::-webkit-meter-bar]:bg-surface-raised [&::-webkit-meter-even-less-good-value]:rounded-md [&::-webkit-meter-even-less-good-value]:bg-bad [&::-webkit-meter-optimum-value]:rounded-md [&::-webkit-meter-optimum-value]:bg-good [&::-webkit-meter-suboptimum-value]:rounded-md [&::-webkit-meter-suboptimum-value]:bg-warn"
    />
  );
}
