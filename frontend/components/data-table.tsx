import type { ReactNode } from "react";

export type TableColumn<T> = {
  label: string;
  render: (row: T) => ReactNode;
  align?: "left" | "right";
};

export function DataTable<T>({ rows, columns, rowKey }: { rows: T[]; columns: TableColumn<T>[]; rowKey: (row: T, index: number) => string }) {
  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead><tr>{columns.map((column) => <th key={column.label} className={column.align === "right" ? "text-right" : "text-left"}>{column.label}</th>)}</tr></thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={rowKey(row, index)}>{columns.map((column) => <td key={column.label} className={column.align === "right" ? "text-right tabular-nums" : "text-left"}>{column.render(row)}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
