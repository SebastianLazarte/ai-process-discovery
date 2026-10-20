// Shared button looks, for <button> and for links styled as buttons, as in web/styles.css.
// 44 px tall, the minimum touch target of the design brief.
const base =
  "inline-flex min-h-11 items-center justify-center gap-2 whitespace-nowrap rounded-control border px-4 text-sm font-semibold no-underline hover:no-underline hover:brightness-115 disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:brightness-100";

const variants = {
  primary: "border-accent bg-accent text-accent-ink",
  secondary: "border-line bg-transparent text-ink",
  danger: "border-line bg-transparent text-bad",
  quiet: "border-transparent bg-transparent text-muted",
} as const;

export function buttonClass(variant: keyof typeof variants = "secondary"): string {
  return `${base} ${variants[variant]}`;
}
