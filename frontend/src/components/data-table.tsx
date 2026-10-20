import type { ReactNode } from "react";

// The table of the vanilla client: uppercase heads, soft row lines, and a horizontal
// scroll on narrow screens instead of a page that overflows.

export type Column<Row> = {
  header: ReactNode;
  cell: (row: Row) => ReactNode;
  /** Figures align right and use tabular digits. */
  numeric?: boolean;
  className?: string;
};

const HEAD =
  "border-b border-line px-2.5 py-2.5 text-[10px] font-medium tracking-[1px] whitespace-nowrap text-table-head uppercase";
const CELL = "border-b border-line-soft px-2.5 py-3 align-top";

export function DataTable<Row>({
  labelledBy,
  columns,
  rows,
  rowKey,
}: {
  /** The id of the heading that names the table. */
  labelledBy: string;
  columns: readonly Column<Row>[];
  rows: readonly Row[];
  rowKey: (row: Row) => string;
}) {
  return (
    <div className="overflow-x-auto">
      <table aria-labelledby={labelledBy} className="w-full border-collapse text-[13px]">
        <thead>
          <tr>
            {columns.map((column, index) => (
              <th
                key={index}
                scope="col"
                className={`${HEAD} ${column.numeric ? "text-right" : "text-left"}`}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)}>
              {columns.map((column, index) => (
                <td
                  key={index}
                  className={`${CELL} ${column.numeric ? "text-right tabular-nums" : ""} ${column.className ?? ""}`}
                >
                  {column.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Three grey rows while a list loads, hidden from screen readers. */
export function SkeletonRows({ rows = 3 }: { rows?: number }) {
  return (
    <ul aria-hidden="true" className="space-y-3">
      {Array.from({ length: rows }, (_, row) => (
        <li
          key={row}
          className="h-12 animate-pulse rounded-control bg-surface-raised motion-reduce:animate-none"
        />
      ))}
    </ul>
  );
}
