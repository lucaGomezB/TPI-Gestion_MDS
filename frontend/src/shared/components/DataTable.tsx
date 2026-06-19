import type { ReactNode } from 'react';

interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (item: T) => ReactNode;
  sortable?: boolean;
  align?: 'left' | 'center' | 'right';
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  isLoading?: boolean;
  emptyMessage?: string;
  onSort?: (key: string) => void;
  sortKey?: string;
  sortDirection?: 'asc' | 'desc';
}

const alignClasses: Record<string, string> = {
  left: 'text-left',
  center: 'text-center',
  right: 'text-right',
};

function SkeletonRow({ columns }: { columns: number }) {
  return (
    <tr className="animate-pulse">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-6 py-4">
          <div className="h-4 bg-tertiary/10 rounded w-3/4" />
        </td>
      ))}
    </tr>
  );
}

function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  isLoading = false,
  emptyMessage = 'No hay datos',
  onSort,
  sortKey,
  sortDirection,
}: DataTableProps<T>): ReactNode {
  function renderSortIndicator(column: Column<T>): ReactNode {
    if (!column.sortable) return null;
    const isActive = sortKey === column.key;
    const arrow = isActive ? (sortDirection === 'asc' ? '\u25B2' : '\u25BC') : '\u25B2';
    return (
      <span
        className={`ml-1 inline-block text-xs ${isActive ? 'text-primary' : 'text-tertiary/50'}`}
      >
        {arrow}
      </span>
    );
  }

  if (isLoading) {
    return (
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={String(col.key)}
                  className={`px-6 py-4 text-label-sm text-secondary font-medium ${alignClasses[col.align ?? 'left']}`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 5 }).map((_, i) => (
              <SkeletonRow key={i} columns={columns.length} />
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-body-sm text-tertiary">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className={`px-6 py-4 text-label-sm text-secondary font-medium border-b border-tertiary/10 ${alignClasses[col.align ?? 'left']} ${col.sortable ? 'cursor-pointer hover:text-primary' : ''}`}
                onClick={() => {
                  if (col.sortable && onSort) {
                    onSort(String(col.key));
                  }
                }}
                role="columnheader"
              >
                <span className="inline-flex items-center">
                  {col.header}
                  {renderSortIndicator(col)}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item, rowIndex) => (
            <tr
              key={rowIndex}
              className="border-b border-tertiary/10 last:border-b-0"
            >
              {columns.map((col) => (
                <td
                  key={String(col.key)}
                  className={`px-6 py-4 text-body-sm text-on-surface ${alignClasses[col.align ?? 'left']}`}
                >
                  {col.render
                    ? col.render(item)
                    : String(item[col.key as keyof T] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export { DataTable };
export default DataTable;
