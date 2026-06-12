import type { ReactNode } from 'react';

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T) => string;
  onEdit?: (item: T) => void;
  onToggle?: (item: T) => void;
  toggleLabel?: (item: T) => string;
  toggleActive?: (item: T) => boolean;
  actions?: (item: T) => ReactNode;
}

function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  keyExtractor,
  onEdit,
  onToggle,
  toggleLabel,
  toggleActive,
  actions,
}: DataTableProps<T>) {
  return (
    <div className="overflow-x-auto bg-white rounded-lg shadow-sm border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider ${col.className || ''}`}
              >
                {col.header}
              </th>
            ))}
            {(onEdit || onToggle || actions) && (
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Acciones
              </th>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {data.map((item) => (
            <tr key={keyExtractor(item)} className="hover:bg-gray-50 transition-colors">
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={`px-4 py-3 text-sm text-gray-700 ${col.className || ''}`}
                >
                  {col.render ? col.render(item) : String(item[col.key] ?? '')}
                </td>
              ))}
              {(onEdit || onToggle || actions) && (
                <td className="px-4 py-3 text-right text-sm">
                  <div className="flex items-center justify-end space-x-2">
                    {onToggle &&
                      toggleLabel &&
                      toggleActive !== undefined && (
                        <button
                          onClick={() => onToggle(item)}
                          className={`px-2 py-1 text-xs font-medium rounded-full transition-colors ${
                            toggleActive(item)
                              ? 'bg-green-100 text-green-700 hover:bg-green-200'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          {toggleLabel(item)}
                        </button>
                      )}
                    {onEdit && (
                      <button
                        onClick={() => onEdit(item)}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors"
                      >
                        Editar
                      </button>
                    )}
                    {actions && actions(item)}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable;
