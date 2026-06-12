import { useState, useCallback, type ReactNode } from 'react';
import type { AuditFilters } from '../types';
import { auditoriaService } from '../services/auditoriaService';

interface AuditExportButtonProps {
  filters: AuditFilters;
  disabled?: boolean;
}

function AuditExportButton({
  filters,
  disabled = false,
}: AuditExportButtonProps): ReactNode {
  const [isOpen, setIsOpen] = useState(false);

  const handleExport = useCallback(
    (formato: 'csv' | 'json') => {
      const url = auditoriaService.exportUrl(filters, formato);
      window.open(url, '_blank');
      setIsOpen(false);
    },
    [filters],
  );

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
          />
        </svg>
        Exportar
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-1 w-40 bg-white border border-gray-200 rounded-md shadow-lg z-20">
            <button
              onClick={() => handleExport('csv')}
              className="w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 text-left transition-colors"
            >
              Exportar CSV
            </button>
            <button
              onClick={() => handleExport('json')}
              className="w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 text-left transition-colors"
            >
              Exportar JSON
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default AuditExportButton;
