import { useState } from 'react';
import { Outlet, Link } from 'react-router-dom';
import { useAuth } from '../features/auth/context/AuthContext';
import Sidebar from './Sidebar';

function MainLayout() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { user, logout } = useAuth();

  const handleToggle = () => setIsCollapsed((prev) => !prev);

  const fullName = user ? `${user.nombre} ${user.apellido}` : '';

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar isCollapsed={isCollapsed} onToggle={handleToggle} />

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
          <div />
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-700">{fullName}</span>
            <div className="flex items-center space-x-2">
              <Link
                to="/perfil"
                className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                Perfil
              </Link>
              <button
                onClick={logout}
                className="text-sm text-red-600 hover:text-red-700 transition-colors"
              >
                Cerrar Sesión
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default MainLayout;
