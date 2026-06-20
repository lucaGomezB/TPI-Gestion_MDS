import { useState, useEffect, useCallback, type ReactNode } from 'react';
import PageHeader from '../../../shared/components/PageHeader';
import Loading from '../../../shared/components/Loading';
import ErrorDisplay from '../../../shared/components/ErrorDisplay';
import Modal from '../../../shared/components/Modal';
import RolesList from '../components/RolesList';
import RolForm from '../components/RolForm';
import type { RolFormValues } from '../components/RolForm';
import type { RolResponse, ModuloPermisos } from '../types';
import { rolesService } from '../services/rolesService';

function AdminRolesPage(): ReactNode {
  const [roles, setRoles] = useState<RolResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modulosPermisos, setModulosPermisos] = useState<ModuloPermisos[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editTarget, setEditTarget] = useState<RolResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchRoles = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await rolesService.list();
      setRoles(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar roles');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchPermissions = useCallback(async () => {
    try {
      const data = await rolesService.getPermissions();
      setModulosPermisos(data.modulos);
    } catch {
      // Permissions load is non-blocking
    }
  }, []);

  useEffect(() => {
    fetchRoles();
    fetchPermissions();
  }, [fetchRoles, fetchPermissions]);

  async function handleCreate(data: RolFormValues): Promise<void> {
    setIsSubmitting(true);
    try {
      await rolesService.create({
        nombre: data.nombre,
        descripcion: data.descripcion || undefined,
        permisos: data.permisos,
      });
      setShowCreateModal(false);
      await fetchRoles();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al crear rol');
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleUpdate(data: RolFormValues): Promise<void> {
    if (!editTarget) return;
    setIsSubmitting(true);
    try {
      await rolesService.update(editTarget.id, {
        nombre: data.nombre !== editTarget.nombre ? data.nombre : undefined,
        descripcion: data.descripcion !== (editTarget.descripcion ?? '')
          ? data.descripcion || undefined
          : undefined,
        permisos: data.permisos,
      });
      setEditTarget(null);
      await fetchRoles();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al actualizar rol');
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete(rol: RolResponse): Promise<void> {
    if (!window.confirm(`Eliminar el rol "${rol.nombre}"? Esta accion no se puede deshacer.`)) return;
    try {
      await rolesService.remove(rol.id);
      await fetchRoles();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al eliminar rol');
    }
  }

  if (error) {
    return (
      <div className="p-6">
        <PageHeader
          title="Roles y Permisos"
          breadcrumbs={[{ label: 'Administracion' }, { label: 'Roles y Permisos' }]}
        />
        <ErrorDisplay message={error} onRetry={fetchRoles} />
      </div>
    );
  }

  return (
    <div className="p-6">
      <PageHeader
        title="Roles y Permisos"
        breadcrumbs={[{ label: 'Administracion' }, { label: 'Roles y Permisos' }]}
        actions={[
          {
            label: 'Nuevo rol',
            onClick: () => setShowCreateModal(true),
          },
        ]}
      />

      {isLoading ? (
        <Loading message="Cargando roles..." />
      ) : (
        <RolesList
          roles={roles}
          isLoading={false}
          onEdit={setEditTarget}
          onDelete={handleDelete}
        />
      )}

      {/* Create modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Crear rol"
        size="lg"
      >
        <RolForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreateModal(false)}
          modulosPermisos={modulosPermisos}
          isSubmitting={isSubmitting}
        />
      </Modal>

      {/* Edit modal */}
      <Modal
        isOpen={editTarget !== null}
        onClose={() => setEditTarget(null)}
        title="Editar rol"
        size="lg"
      >
        {editTarget && (
          <RolForm
            key={editTarget.id}
            onSubmit={handleUpdate}
            onCancel={() => setEditTarget(null)}
            initialData={editTarget}
            modulosPermisos={modulosPermisos}
            isSubmitting={isSubmitting}
          />
        )}
      </Modal>
    </div>
  );
}

export default AdminRolesPage;
