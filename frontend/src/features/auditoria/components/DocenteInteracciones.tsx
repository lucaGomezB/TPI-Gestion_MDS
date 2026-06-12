import { useState, useCallback, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { useDocenteInteracciones } from '../hooks/useDocenteInteracciones';
import { ACCIONES_LABELS } from '../types';
import Loading from '../../../shared/components/Loading';
import ErrorDisplay from '../../../shared/components/ErrorDisplay';
import EmptyState from '../../../shared/components/EmptyState';

function DocenteInteracciones(): ReactNode {
  const [docenteId, setDocenteId] = useState<string | undefined>(undefined);
  const [searchTerm, setSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);

  const { data, isLoading, isError, error, refetch } =
    useDocenteInteracciones(docenteId);

  const handleSelectDocente = useCallback(
    (id: string, nombre: string) => {
      setDocenteId(id);
      setSearchTerm(nombre);
      setShowDropdown(false);
    },
    [],
  );

  // Mock docente search — in production, this would query a users endpoint
  const mockDocentes = [
    { id: '1', nombre: 'Juan Pérez' },
    { id: '2', nombre: 'María García' },
    { id: '3', nombre: 'Carlos López' },
  ];

  const filteredDocentes = mockDocentes.filter((d) =>
    d.nombre.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Interacciones por Docente
      </h3>

      {/* Teacher typeahead */}
      <div className="relative mb-4">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setShowDropdown(true);
            if (!e.target.value) {
              setDocenteId(undefined);
            }
          }}
          onFocus={() => setShowDropdown(true)}
          placeholder="Buscar docente por nombre..."
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          aria-label="Buscar docente"
        />
        {showDropdown && searchTerm && filteredDocentes.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-48 overflow-y-auto">
            {filteredDocentes.map((docente) => (
              <button
                key={docente.id}
                onClick={() =>
                  handleSelectDocente(docente.id, docente.nombre)
                }
                className="w-full px-4 py-2 text-sm text-left text-gray-700 hover:bg-blue-50 transition-colors"
              >
                {docente.nombre}
              </button>
            ))}
          </div>
        )}
        {showDropdown && searchTerm && filteredDocentes.length === 0 && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg p-3 text-sm text-gray-500 text-center">
            No se encontraron docentes
          </div>
        )}
      </div>

      {/* Teacher data panel */}
      {!docenteId && (
        <EmptyState
          title="Seleccione un docente"
          description="Busque y seleccione un docente para ver sus interacciones."
        />
      )}

      {isLoading && (
        <Loading message="Cargando interacciones del docente..." />
      )}

      {isError && (
        <ErrorDisplay
          message={
            error?.message || 'Error al cargar las interacciones del docente'
          }
          onRetry={() => refetch()}
        />
      )}

      {data && !isLoading && !isError && (
        <div className="space-y-4">
          {/* Summary cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-blue-50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-blue-700">
                {data.total_acciones}
              </p>
              <p className="text-xs text-blue-600 font-medium">
                Total de acciones
              </p>
            </div>
            <div className="bg-green-50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-green-700">
                {Object.keys(data.por_accion).length}
              </p>
              <p className="text-xs text-green-600 font-medium">
                Tipos de acción
              </p>
            </div>
            <div className="bg-purple-50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-purple-700">
                {data.por_materia.length}
              </p>
              <p className="text-xs text-purple-600 font-medium">Materias</p>
            </div>
          </div>

          {/* Breakdown by action type */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">
              Desglose por acción
            </h4>
            <div className="space-y-1">
              {Object.entries(data.por_accion).map(([accion, count]) => (
                <div
                  key={accion}
                  className="flex items-center justify-between px-3 py-1.5 bg-gray-50 rounded text-sm"
                >
                  <span className="text-gray-700">
                    {ACCIONES_LABELS[accion] || accion}
                  </span>
                  <span className="font-medium text-gray-900">{count}</span>
                </div>
              ))}
              {Object.keys(data.por_accion).length === 0 && (
                <p className="text-sm text-gray-400 italic">
                  No hay acciones registradas
                </p>
              )}
            </div>
          </div>

          {/* Actions by materia */}
          {data.por_materia.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Acciones por materia
              </h4>
              <div className="space-y-1">
                {data.por_materia.map((m) => (
                  <div
                    key={m.materia_id}
                    className="flex items-center justify-between px-3 py-1.5 bg-gray-50 rounded text-sm"
                  >
                    <span className="text-gray-700">{m.nombre}</span>
                    <span className="font-medium text-gray-900">
                      {m.total}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Last N actions */}
          {data.ultimas_acciones.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Últimas acciones
              </h4>
              <ul className="space-y-1">
                {data.ultimas_acciones.slice(0, 10).map((accion) => (
                  <li
                    key={accion.id}
                    className="px-3 py-2 bg-gray-50 rounded text-xs text-gray-600"
                  >
                    <span className="font-medium">
                      {new Date(accion.fecha_hora).toLocaleDateString(
                        'es-AR',
                        {
                          day: '2-digit',
                          month: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit',
                        },
                      )}
                    </span>{' '}
                    - {ACCIONES_LABELS[accion.accion] || accion.accion}
                    {accion.materia_nombre && (
                      <span className="text-gray-400">
                        {' '}
                        · {accion.materia_nombre}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Link to full log */}
          {data.total_acciones > 0 && (
            <div className="pt-2">
              <Link
                to={`/admin/auditoria?actor_id=${docenteId}`}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
              >
                Ver en el log completo →
              </Link>
            </div>
          )}
        </div>
      )}

      {data && data.total_acciones === 0 && !isLoading && (
        <EmptyState
          title="Sin interacciones"
          description="El docente no tiene interacciones registradas."
        />
      )}
    </div>
  );
}

export default DocenteInteracciones;
