// The mark of web/icon.svg, coloured from tokens so it follows the theme.
export function BrandIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true" className={className}>
      <rect width="64" height="64" rx="14" fill="var(--icon-bg)" />
      <circle cx="18" cy="20" r="6" fill="var(--accent)" />
      <circle cx="46" cy="32" r="6" fill="var(--accent)" opacity=".7" />
      <circle cx="18" cy="44" r="6" fill="var(--accent)" opacity=".45" />
      <path
        d="M24 20h8a8 8 0 0 1 8 8v4M24 44h8a8 8 0 0 0 8-8"
        stroke="var(--accent)"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
      />
    </svg>
  );
}
