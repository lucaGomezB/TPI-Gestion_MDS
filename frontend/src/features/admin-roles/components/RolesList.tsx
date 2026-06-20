import type { ReactNode } from 'react';
import DataTable from '../../../shared/components/DataTable';
import Badge from '../../../shared/components/Badge';
import Button from '../../../shared/components/Button';
import type { RolResponse } from '../types';

function permissionBadgeVariant(_perm: string): 'info' | 'neutral' {
  return 'info';
}

interface RolesListProps {
  roles: RolResponse[];
  isLoading: boolean;
  onEdit: (rol: RolResponse) => void;
  onDelete: (rol: RolResponse) => void;
}

function RolesList({ roles, isLoading, onEdit, onDelete }: RolesListProps) {
  const columns = [
    {
      key: 'nombre' as const,
      header: 'Rol',
      render: (item: RolResponse): ReactNode => (
        <div>
          <span className="font-medium text-gray-900">{item.nombre}</span>
          {item.descripcion && (
            <p className="text-xs text-gray-500 mt-0.5">{item.descripcion}</p>
          )}
        </div>
      ),
    },
    {
      key: 'permisos' as const,
      header: 'Permisos',
      render: (item: RolResponse): ReactNode => (
        <div className="flex flex-wrap gap-1 max-w-md">
          {item.permisos.length === 0 ? (
            <span className="text-gray-400 text-xs">Sin permisos</span>
          ) : (
            item.permisos.map((perm) => (
              <Badge key={perm} variant={permissionBadgeVariant(perm)}>
                {perm}
              </Badge>
            ))
          )}
        </div>
      ),
    },
    {
      key: 'activo' as const,
      header: 'Activo',
      align: 'center' as const,
      render: (item: RolResponse): ReactNode => (
        <Badge variant={item.activo ? 'success' : 'error'}>
          {item.activo ? 'Activo' : 'Inactivo'}
        </Badge>
      ),
    },
    {
      key: 'acciones' as const,
      header: 'Acciones',
      align: 'right' as const,
      render: (item: RolResponse): ReactNode => (
        <div className="flex items-center justify-end gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEdit(item)}
          >
            Editar
          </Button>
          {item.activo && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete(item)}
              className="text-red-600 hover:bg-red-50"
            >
              Eliminar
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={roles}
      isLoading={isLoading}
      emptyMessage="No se encontraron roles"
    />
  );
}

export default RolesList;
