// Shared button looks, for <button> and for links styled as buttons. 44 px tall, the
// minimum touch target of the design brief.
const base =
  "inline-flex min-h-11 items-center justify-center rounded-md px-4 text-sm font-medium disabled:opacity-60";

const variants = {
  primary: "bg-blue-700 text-white hover:bg-blue-800",
  secondary: "border border-gray-300 bg-white text-gray-900 hover:bg-gray-50",
  danger: "border border-red-700 bg-white text-red-800 hover:bg-red-50",
} as const;

export function buttonClass(variant: keyof typeof variants = "secondary"): string {
  return `${base} ${variants[variant]}`;
}
