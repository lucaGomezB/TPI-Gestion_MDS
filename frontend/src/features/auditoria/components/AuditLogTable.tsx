import { useState, Fragment, type ReactNode } from 'react';
import type { AuditEntry } from '../types';
import { ACCIONES_LABELS } from '../types';
import EmptyState from '../../../shared/components/EmptyState';

interface AuditLogTableProps {
  items: AuditEntry[];
  isLoading: boolean;
  isFetching: boolean;
}

function formatFechaHora(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getAccionLabel(accion: string): string {
  return ACCIONES_LABELS[accion] || accion;
}

interface RowDetailProps {
  entry: AuditEntry;
}

function RowDetail({ entry }: RowDetailProps): ReactNode {
  return (
    <td
      colSpan={7}
      className="px-6 py-4 bg-gray-50 border-t border-gray-200"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div>
          <h4 className="font-medium text-gray-700 mb-2">Detalle</h4>
          {entry.detalle && Object.keys(entry.detalle).length > 0 ? (
            <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto max-h-48">
              {JSON.stringify(entry.detalle, null, 2)}
            </pre>
          ) : (
            <p className="text-gray-400 italic">Sin detalle adicional</p>
          )}
        </div>
        <div className="space-y-2">
          {entry.user_agent && (
            <div>
              <span className="font-medium text-gray-700">
                User Agent:
              </span>
              <p className="text-gray-600 truncate" title={entry.user_agent}>
                {entry.user_agent}
              </p>
            </div>
          )}
          {entry.impersonado_id && (
            <div>
              <span className="font-medium text-gray-700">
                Actuando como:
              </span>
              <p className="text-gray-600">
                {entry.impersonado_nombre || entry.impersonado_id}
              </p>
            </div>
          )}
          {entry.filas_afectadas !== undefined && (
            <div>
              <span className="font-medium text-gray-700">
                Filas afectadas:
              </span>
              <p className="text-gray-600">{entry.filas_afectadas}</p>
            </div>
          )}
        </div>
      </div>
    </td>
  );
}

function AuditLogTable({
  items,
  isLoading,
  isFetching,
}: AuditLogTableProps): ReactNode {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleRow = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  if (!isLoading && items.length === 0) {
    return (
      <EmptyState
        title="No se encontraron resultados"
        description="No hay entradas de auditoría que coincidan con los filtros aplicados."
      />
    );
  }

  return (
    <div
      className={`overflow-x-auto bg-white rounded-lg border border-gray-200 ${
        isFetching ? 'opacity-60 transition-opacity' : ''
      }`}
    >
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Fecha / Hora
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Usuario
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Acción
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Materia
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              IP
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Filas
            </th>
            <th className="px-4 py-3 w-8" />
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {items.map((entry) => {
            const isExpanded = expandedId === entry.id;
            return (
              <Fragment key={entry.id}>
                <tr
                  className="group cursor-pointer hover:bg-gray-50"
                  onClick={() => toggleRow(entry.id)}
                >
                  <td className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap">
                    {formatFechaHora(entry.fecha_hora)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap">
                    {entry.actor_nombre || entry.actor_id}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span
                      className="inline-block px-2 py-1 text-xs font-medium bg-blue-50 text-blue-700 rounded-full"
                      title={`Código: ${entry.accion}`}
                    >
                      {getAccionLabel(entry.accion)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                    {entry.materia_nombre || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 font-mono whitespace-nowrap">
                    {entry.ip || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900 text-right whitespace-nowrap">
                    {entry.filas_afectadas ?? '-'}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleRow(entry.id);
                      }}
                      className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                      aria-label={
                        isExpanded ? 'Contraer detalle' : 'Expandir detalle'
                      }
                    >
                      <svg
                        className={`w-4 h-4 transition-transform ${
                          isExpanded ? 'rotate-180' : ''
                        }`}
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={2}
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M19.5 8.25l-7.5 7.5-7.5-7.5"
                        />
                      </svg>
                    </button>
                  </td>
                </tr>
                {isExpanded && (
                  <tr key={`detail-${entry.id}`}>
                    <RowDetail entry={entry} />
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default AuditLogTable;
