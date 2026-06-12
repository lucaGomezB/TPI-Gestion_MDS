import { type ReactNode } from 'react';
import { PAGE_SIZES } from '../types';

interface AuditPaginationProps {
  total: number;
  offset: number;
  limit: number;
  onPageChange: (offset: number) => void;
  onPageSizeChange: (limit: number) => void;
}

function AuditPagination({
  total,
  offset,
  limit,
  onPageChange,
  onPageSizeChange,
}: AuditPaginationProps): ReactNode {
  const currentPageStart = offset + 1;
  const currentPageEnd = Math.min(offset + limit, total);
  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  const hasNext = offset + limit < total;
  const hasPrev = offset > 0;

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mt-4 px-1">
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-600">
          {total > 0
            ? `${currentPageStart}-${currentPageEnd} de ${total} resultados`
            : '0 resultados'}
        </span>
        <select
          value={limit}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          className="px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Resultados por página"
        >
          {PAGE_SIZES.map((size) => (
            <option key={size} value={size}>
              {size} / pág
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-500">
          Pág. {currentPage} de {totalPages || 1}
        </span>
        <button
          onClick={() => onPageChange(offset - limit)}
          disabled={!hasPrev}
          className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Anterior
        </button>
        <button
          onClick={() => onPageChange(offset + limit)}
          disabled={!hasNext}
          className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Siguiente
        </button>
      </div>
    </div>
  );
}

export default AuditPagination;
