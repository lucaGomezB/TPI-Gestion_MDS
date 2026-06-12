import type { ReactNode } from 'react';

interface PermissionDeniedProps {
  requiredPermission?: string;
}

function PermissionDenied({ requiredPermission }: PermissionDeniedProps): ReactNode {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <svg className="w-16 h-16 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
      </svg>
      <h3 className="text-lg font-medium text-gray-900 mb-1">Acceso denegado</h3>
      <p className="text-sm text-gray-500 max-w-sm">
        {requiredPermission
          ? `Necesitas el permiso "${requiredPermission}" para acceder a esta pagina.`
          : 'No tienes los permisos necesarios para acceder a esta pagina.'}
      </p>
    </div>
  );
}

export default PermissionDenied;
