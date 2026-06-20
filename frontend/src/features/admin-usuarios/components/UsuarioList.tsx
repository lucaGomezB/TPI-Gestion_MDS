import type { ReactNode } from 'react';
import DataTable from '../../../shared/components/DataTable';
import Badge from '../../../shared/components/Badge';
import Button from '../../../shared/components/Button';
import type { UsuarioResponse } from '../types';

function roleBadgeVariant(role: string): 'success' | 'warning' | 'error' | 'info' | 'neutral' {
  const map: Record<string, 'success' | 'warning' | 'error' | 'info' | 'neutral'> = {
    ADMIN: 'error',
    COORDINADOR: 'warning',
    PROFESOR: 'info',
    TUTOR: 'success',
    NEXO: 'neutral',
    FINANZAS: 'warning',
    ALUMNO: 'neutral',
  };
  return map[role] ?? 'neutral';
}

interface UsuarioListProps {
  usuarios: UsuarioResponse[];
  isLoading: boolean;
  onEdit: (usuario: UsuarioResponse) => void;
  onDeactivate: (usuario: UsuarioResponse) => void;
}

function UsuarioList({ usuarios, isLoading, onEdit, onDeactivate }: UsuarioListProps) {
  const columns = [
    {
      key: 'nombre' as const,
      header: 'Nombre',
      render: (item: UsuarioResponse): ReactNode => (
        <span className="font-medium text-gray-900">
          {item.nombre} {item.apellidos}
        </span>
      ),
    },
    {
      key: 'email' as const,
      header: 'Email',
    },
    {
      key: 'roles' as const,
      header: 'Roles',
      render: (item: UsuarioResponse): ReactNode => (
        <div className="flex flex-wrap gap-1">
          {item.roles.length === 0 ? (
            <span className="text-gray-400 text-xs">Sin roles</span>
          ) : (
            item.roles.map((rol) => (
              <Badge key={rol} variant={roleBadgeVariant(rol)}>
                {rol}
              </Badge>
            ))
          )}
        </div>
      ),
    },
    {
      key: 'facturador' as const,
      header: 'Facturador',
      align: 'center' as const,
      render: (item: UsuarioResponse): ReactNode => (
        <span className={item.facturador ? 'text-green-600 font-medium' : 'text-gray-400'}>
          {item.facturador ? 'Si' : 'No'}
        </span>
      ),
    },
    {
      key: 'activo' as const,
      header: 'Activo',
      align: 'center' as const,
      render: (item: UsuarioResponse): ReactNode => (
        <Badge variant={item.activo ? 'success' : 'error'}>
          {item.activo ? 'Activo' : 'Inactivo'}
        </Badge>
      ),
    },
    {
      key: 'acciones' as const,
      header: 'Acciones',
      align: 'right' as const,
      render: (item: UsuarioResponse): ReactNode => (
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
              onClick={() => onDeactivate(item)}
              className="text-red-600 hover:bg-red-50"
            >
              Desactivar
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={usuarios}
      isLoading={isLoading}
      emptyMessage="No se encontraron usuarios"
    />
  );
}

export default UsuarioList;
