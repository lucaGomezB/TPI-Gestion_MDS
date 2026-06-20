import { useState, useEffect, useCallback, type ReactNode } from 'react';
import PageHeader from '../../../shared/components/PageHeader';
import Loading from '../../../shared/components/Loading';
import ErrorDisplay from '../../../shared/components/ErrorDisplay';
import EmptyState from '../../../shared/components/EmptyState';
import Badge from '../../../shared/components/Badge';
import DataTable from '../../../shared/components/DataTable';
import Modal from '../../../shared/components/Modal';
import TareaForm from '../components/TareaForm';
import type { TareaFormValues } from '../components/TareaForm';
import ComentarioThread from '../components/ComentarioThread';
import { tareasService } from '../services/tareasService';
import type {
  TareaResponse,
  ComentarioResponse,
} from '../types';
import { ESTADOS_TAREA, ESTADO_VARIANT_MAP, getNextEstados } from '../types';

function formatDateShort(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  });
}

function TareasPage(): ReactNode {
  const [tareas, setTareas] = useState<TareaResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [estadoFilter, setEstadoFilter] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [comentariosTarget, setComentariosTarget] =
    useState<TareaResponse | null>(null);
  const [comentariosCache, setComentariosCache] = useState<
    Record<string, ComentarioResponse[]>
  >({});
  const [estadoChanging, setEstadoChanging] = useState<Record<string, boolean>>(
    {},
  );

  const fetchTareas = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await tareasService.list(
        estadoFilter || undefined,
      );
      setTareas(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Error al cargar tareas',
      );
    } finally {
      setIsLoading(false);
    }
  }, [estadoFilter]);

  useEffect(() => {
    fetchTareas();
  }, [fetchTareas]);

  async function handleCreate(data: TareaFormValues): Promise<void> {
    setIsSubmitting(true);
    try {
      await tareasService.create({
        asignado_a: data.asignado_a,
        descripcion: data.descripcion,
        materia_id: data.materia_id || undefined,
        contexto_id: data.contexto_id || undefined,
      });
      setShowCreateModal(false);
      await fetchTareas();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Error al crear tarea',
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleChangeEstado(
    tarea: TareaResponse,
    nuevoEstado: string,
  ): Promise<void> {
    setEstadoChanging((prev) => ({ ...prev, [tarea.id]: true }));
    try {
      const updated = await tareasService.changeEstado(tarea.id, {
        estado: nuevoEstado,
      });
      setTareas((prev) =>
        prev.map((t) => (t.id === updated.id ? updated : t)),
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Error al cambiar estado',
      );
    } finally {
      setEstadoChanging((prev) => ({ ...prev, [tarea.id]: false }));
    }
  }

  function handleOpenComentarios(tarea: TareaResponse): void {
    setComentariosTarget(tarea);
    if (!comentariosCache[tarea.id]) {
      setComentariosCache((prev) => ({
        ...prev,
        [tarea.id]: [],
      }));
    }
  }

  function handleComentarioAdded(comentario: ComentarioResponse): void {
    setComentariosCache((prev) => ({
      ...prev,
      [comentario.tarea_id]: [
        ...(prev[comentario.tarea_id] || []),
        comentario,
      ],
    }));
  }

  function describeTareaDescripcion(descripcion: string, maxLen = 60): string {
    return descripcion.length > maxLen
      ? descripcion.substring(0, maxLen) + '...'
      : descripcion;
  }

  const columns = [
    {
      key: 'descripcion' as const,
      header: 'Descripcion',
      render: (t: TareaResponse) => (
        <span
          className="text-sm text-gray-900"
          title={t.descripcion}
        >
          {describeTareaDescripcion(t.descripcion)}
        </span>
      ),
    },
    {
      key: 'asignado_a' as const,
      header: 'Asignado a',
      render: (t: TareaResponse) => (
        <span className="text-xs text-gray-500 font-mono">
          {t.asignado_a.substring(0, 8)}...
        </span>
      ),
    },
    {
      key: 'estado' as const,
      header: 'Estado',
      render: (t: TareaResponse) => (
        <Badge variant={ESTADO_VARIANT_MAP[t.estado] || 'neutral'}>
          {t.estado}
        </Badge>
      ),
    },
    {
      key: 'created_at' as const,
      header: 'Creado',
      render: (t: TareaResponse) => (
        <span className="text-xs text-gray-500">
          {formatDateShort(t.created_at)}
        </span>
      ),
    },
    {
      key: 'acciones' as const,
      header: 'Acciones',
      render: (t: TareaResponse) => {
        const next = getNextEstados(t.estado);
        const isChanging = estadoChanging[t.id] || false;

        return (
          <div className="flex items-center gap-1 flex-wrap">
            {next.map((est) => (
              <button
                key={est}
                onClick={() => handleChangeEstado(t, est)}
                disabled={isChanging}
                className={`px-2 py-1 text-xs rounded font-medium transition-colors disabled:opacity-50 ${
                  est === 'Cancelada'
                    ? 'bg-red-50 text-red-700 hover:bg-red-100 border border-red-200'
                    : 'bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200'
                }`}
                title={
                  est === 'Cancelada'
                    ? 'Cancelar tarea'
                    : `Mover a ${est}`
                }
              >
                {est === 'Cancelada'
                  ? 'Cancelar'
                  : t.estado === 'Pendiente'
                    ? 'Iniciar'
                    : 'Resolver'}
              </button>
            ))}
            <button
              onClick={() => handleOpenComentarios(t)}
              className="px-2 py-1 text-xs rounded font-medium bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200 transition-colors"
              title="Ver comentarios"
            >
              Coment.
            </button>
          </div>
        );
      },
    },
  ];

  if (error) {
    return (
      <div className="p-6">
        <PageHeader
          title="Tareas Internas"
          breadcrumbs={[{ label: 'Tareas Internas' }]}
        />
        <ErrorDisplay message={error} onRetry={fetchTareas} />
      </div>
    );
  }

  return (
    <div className="p-6">
      <PageHeader
        title="Tareas Internas"
        breadcrumbs={[{ label: 'Tareas Internas' }]}
        actions={[
          {
            label: 'Nueva tarea',
            onClick: () => setShowCreateModal(true),
          },
        ]}
      />

      {/* Estado filter */}
      <div className="mb-4 flex items-center gap-2">
        <label
          htmlFor="estado-filter"
          className="text-sm text-gray-600"
        >
          Filtrar por estado:
        </label>
        <select
          id="estado-filter"
          value={estadoFilter}
          onChange={(e) => setEstadoFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos</option>
          {ESTADOS_TAREA.map((est) => (
            <option key={est} value={est}>
              {est}
            </option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <Loading message="Cargando tareas..." />
      ) : tareas.length === 0 ? (
        <EmptyState
          title="Sin tareas"
          description={
            estadoFilter
              ? `No hay tareas en estado "${estadoFilter}".`
              : 'No tenes tareas asignadas. Crea una nueva para comenzar.'
          }
          actionLabel="Nueva tarea"
          onAction={() => setShowCreateModal(true)}
        />
      ) : (
        <DataTable
          columns={columns}
          data={tareas as unknown as Record<string, unknown>[]}
          emptyMessage="No se encontraron tareas"
        />
      )}

      {/* Create modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Nueva tarea"
        size="lg"
      >
        <TareaForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreateModal(false)}
          isSubmitting={isSubmitting}
        />
      </Modal>

      {/* Comentarios modal */}
      <Modal
        isOpen={comentariosTarget !== null}
        onClose={() => setComentariosTarget(null)}
        title={
          comentariosTarget
            ? `Comentarios — ${describeTareaDescripcion(comentariosTarget.descripcion, 40)}`
            : 'Comentarios'
        }
        size="lg"
      >
        {comentariosTarget && (
          <ComentarioThread
            key={comentariosTarget.id}
            tareaId={comentariosTarget.id}
            comentarios={
              comentariosCache[comentariosTarget.id] || []
            }
            onComentarioAdded={handleComentarioAdded}
          />
        )}
      </Modal>
    </div>
  );
}

export default TareasPage;
