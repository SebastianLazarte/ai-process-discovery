import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { vi } from "vitest";

import { Providers } from "@/app/providers";

/** Renders inside the app providers (query client, toast), as every page is. */
export function renderWithProviders(ui: ReactElement) {
  return render(<Providers>{ui}</Providers>);
}

/** The router push of next/navigation, mocked by each test file with `mockRouter()`. */
export const push = vi.fn();
