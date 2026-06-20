import { useState, useEffect, useCallback, type ReactNode } from 'react';
import PageHeader from '../../../shared/components/PageHeader';
import Loading from '../../../shared/components/Loading';
import ErrorDisplay from '../../../shared/components/ErrorDisplay';
import Modal from '../../../shared/components/Modal';
import UsuarioList from '../components/UsuarioList';
import UsuarioForm from '../components/UsuarioForm';
import type { UsuarioFormValues } from '../components/UsuarioForm';
import { ROLES_DISPONIBLES } from '../types';
import type { UsuarioResponse } from '../types';
import { usuariosService } from '../services/usuariosService';

function AdminUsuariosPage(): ReactNode {
  const [usuarios, setUsuarios] = useState<UsuarioResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rolFilter, setRolFilter] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editTarget, setEditTarget] = useState<UsuarioResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchUsuarios = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await usuariosService.list(rolFilter || undefined);
      setUsuarios(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar usuarios');
    } finally {
      setIsLoading(false);
    }
  }, [rolFilter]);

  useEffect(() => {
    fetchUsuarios();
  }, [fetchUsuarios]);

  async function handleCreate(data: UsuarioFormValues): Promise<void> {
    setIsSubmitting(true);
    try {
      await usuariosService.create({
        ...data,
        password: data.password || undefined,
      });
      setShowCreateModal(false);
      await fetchUsuarios();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al crear usuario');
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleUpdate(data: UsuarioFormValues): Promise<void> {
    if (!editTarget) return;
    setIsSubmitting(true);
    try {
      await usuariosService.update(editTarget.id, {
        ...data,
        password: data.password || undefined,
      });
      setEditTarget(null);
      await fetchUsuarios();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al actualizar usuario');
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDeactivate(usuario: UsuarioResponse): Promise<void> {
    if (!window.confirm(`Desactivar a ${usuario.nombre} ${usuario.apellidos}?`)) return;
    try {
      await usuariosService.deactivate(usuario.id);
      await fetchUsuarios();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al desactivar usuario');
    }
  }

  if (error) {
    return (
      <div className="p-6">
        <PageHeader
          title="Usuarios"
          breadcrumbs={[{ label: 'Administracion' }, { label: 'Usuarios' }]}
        />
        <ErrorDisplay message={error} onRetry={fetchUsuarios} />
      </div>
    );
  }

  return (
    <div className="p-6">
      <PageHeader
        title="Usuarios"
        breadcrumbs={[{ label: 'Administracion' }, { label: 'Usuarios' }]}
        actions={[
          {
            label: 'Nuevo usuario',
            onClick: () => setShowCreateModal(true),
          },
        ]}
      />

      {/* Role filter */}
      <div className="mb-4 flex items-center gap-2">
        <label htmlFor="rol-filter" className="text-sm text-gray-600">
          Filtrar por rol:
        </label>
        <select
          id="rol-filter"
          value={rolFilter}
          onChange={(e) => setRolFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos</option>
          {ROLES_DISPONIBLES.map((rol) => (
            <option key={rol} value={rol}>
              {rol}
            </option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <Loading message="Cargando usuarios..." />
      ) : (
        <UsuarioList
          usuarios={usuarios}
          isLoading={false}
          onEdit={setEditTarget}
          onDeactivate={handleDeactivate}
        />
      )}

      {/* Create modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Crear usuario"
        size="lg"
      >
        <UsuarioForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreateModal(false)}
          isSubmitting={isSubmitting}
        />
      </Modal>

      {/* Edit modal */}
      <Modal
        isOpen={editTarget !== null}
        onClose={() => setEditTarget(null)}
        title="Editar usuario"
        size="lg"
      >
        {editTarget && (
          <UsuarioForm
            key={editTarget.id}
            onSubmit={handleUpdate}
            onCancel={() => setEditTarget(null)}
            initialData={editTarget}
            isSubmitting={isSubmitting}
          />
        )}
      </Modal>
    </div>
  );
}

export default AdminUsuariosPage;
