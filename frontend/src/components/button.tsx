import type { ButtonHTMLAttributes } from "react";

import { SpinnerIcon } from "./icons";

// Graphite buttons (ADR 0018), for <button> and for links styled as buttons. One primary
// action per view, filled with the accent; secondary actions sit on a raised surface;
// tertiary ones are text. Every variant has the same states: hover, focus-visible,
// disabled and pending (aria-busy). 44 px tall, the minimum touch target of the brief.
const base =
  "inline-flex min-h-11 items-center justify-center gap-2 whitespace-nowrap rounded-control px-4 text-sm font-semibold no-underline transition-colors duration-150 hover:no-underline focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-accent disabled:cursor-not-allowed disabled:opacity-45 aria-busy:cursor-progress";

const variants = {
  primary:
    "bg-accent text-accent-ink hover:bg-accent-hover hover:text-accent-ink disabled:hover:bg-accent",
  secondary:
    "bg-surface-raised text-ink hover:bg-surface-hover hover:text-ink disabled:hover:bg-surface-raised",
  tertiary:
    "bg-transparent text-ink-soft hover:text-ink hover:underline disabled:hover:text-ink-soft disabled:hover:no-underline",
  danger:
    "bg-surface-raised text-bad hover:bg-surface-hover hover:text-bad disabled:hover:bg-surface-raised",
} as const;

export type ButtonVariant = keyof typeof variants;

export function buttonClass(variant: ButtonVariant = "secondary"): string {
  return `${base} ${variants[variant]}`;
}

type ButtonProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "type"> & {
  variant?: ButtonVariant;
  type?: "button" | "submit";
  /** While true the button is disabled, says it is busy and shows a spinner. */
  pending?: boolean;
  /** What the button says while pending, such as "Loading…". Defaults to its children. */
  pendingLabel?: string;
};

export function Button({
  variant = "secondary",
  type = "button",
  pending = false,
  pendingLabel,
  disabled,
  className = "",
  children,
  ...rest
}: ButtonProps) {
  const props = {
    ...rest,
    className: `${buttonClass(variant)} ${className}`.trim(),
    disabled: disabled || pending,
    "aria-busy": pending || undefined,
  };
  const content = (
    <>
      {pending && <SpinnerIcon />}
      {pending && pendingLabel ? pendingLabel : children}
    </>
  );
  return type === "submit" ? (
    <button type="submit" {...props}>
      {content}
    </button>
  ) : (
    <button type="button" {...props}>
      {content}
    </button>
  );
}
