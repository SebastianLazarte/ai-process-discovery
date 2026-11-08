import type { ReactNode } from "react";

// Our own icons (ADR 0018): inline SVG drawn with the stroke of the type, coloured by the
// text around them through currentColor. No icon package. An icon beside its own text is
// decoration and hidden from screen readers; one that stands alone takes a label and is
// announced as an image with that name.

export type IconProps = {
  /** The accessible name, for an icon with no visible text beside it. */
  label?: string;
  className?: string;
};

function Icon({ label, className = "size-5", children }: IconProps & { children: ReactNode }) {
  const a11y = label ? { role: "img", "aria-label": label } : { "aria-hidden": true as const };
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      focusable="false"
      className={`shrink-0 ${className}`}
      {...a11y}
    >
      {label && <title>{label}</title>}
      {children}
    </svg>
  );
}

export function PlusIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 5v14M5 12h14" />
    </Icon>
  );
}

export function HomeIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M3 12 12 3l9 9M5 10v10h14V10" />
    </Icon>
  );
}

export function TemplatesIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </Icon>
  );
}

export function ProcessesIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M4 6h16M4 12h16M4 18h10" />
    </Icon>
  );
}

export function DescribeIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M4 20h4L19 9l-4-4L4 16z" />
    </Icon>
  );
}

export function PlayIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M6 4l13 8-13 8z" />
    </Icon>
  );
}

export function DownloadIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 4v11M7 10l5 5 5-5M5 20h14" />
    </Icon>
  );
}

export function ArrowRightIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </Icon>
  );
}

export function ArrowUpIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 19V5M6 11l6-6 6 6" />
    </Icon>
  );
}

export function ArrowDownIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 5v14M6 13l6 6 6-6" />
    </Icon>
  );
}

export function CheckIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M5 12.5 10 17l9-10" />
    </Icon>
  );
}

export function InfoIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5M12 8h.01" />
    </Icon>
  );
}

export function WarningIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 4 2.5 20h19z" />
      <path d="M12 10v4M12 17h.01" />
    </Icon>
  );
}

export function CloseIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M6 6l12 12M18 6 6 18" />
    </Icon>
  );
}

/** The pending mark of a button. It spins only when the system allows motion. */
export function SpinnerIcon({ className = "size-4", ...props }: IconProps) {
  return (
    <Icon {...props} className={`motion-safe:animate-spin ${className}`}>
      <path d="M12 3a9 9 0 1 0 9 9" />
    </Icon>
  );
}

/** Every icon, for the tests that check each one is hidden or named. */
export const ICONS = {
  PlusIcon,
  HomeIcon,
  TemplatesIcon,
  ProcessesIcon,
  DescribeIcon,
  PlayIcon,
  DownloadIcon,
  ArrowRightIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  CheckIcon,
  InfoIcon,
  WarningIcon,
  CloseIcon,
  SpinnerIcon,
} as const;
