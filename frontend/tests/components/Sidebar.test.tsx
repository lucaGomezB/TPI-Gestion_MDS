import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../../src/features/auth/context/AuthContext';
import Sidebar from '../../src/components/Sidebar';

function renderSidebar(isCollapsed = false, onToggle = () => {}) {
  const user = {
    id: '1',
    email: 'admin@test.com',
    nombre: 'Admin',
    apellido: 'User',
    rol: 'ADMIN',
    tenant_id: 't1',
  };
  localStorage.setItem('access_token', 'valid-token');
  localStorage.setItem('user', JSON.stringify(user));

  return render(
    <MemoryRouter>
      <AuthProvider>
        <Sidebar isCollapsed={isCollapsed} onToggle={onToggle} />
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe('Sidebar', () => {
  it('renders navigation sections', () => {
    renderSidebar();
    expect(screen.getByText('Académico')).toBeInTheDocument();
    expect(screen.getByText('Comunicaciones')).toBeInTheDocument();
    expect(screen.getByText('Administración')).toBeInTheDocument();
    expect(screen.getByText('Reportes')).toBeInTheDocument();
  });

  it('renders navigation items for ADMIN role', () => {
    renderSidebar();
    expect(screen.getByText('Materias')).toBeInTheDocument();
    expect(screen.getByText('Usuarios')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('shows collapsed state when isCollapsed is true', () => {
    renderSidebar(true);
    expect(screen.queryByText('Académico')).not.toBeInTheDocument();
    expect(screen.queryByText('Materias')).not.toBeInTheDocument();
  });

  it('renders the app name when not collapsed', () => {
    renderSidebar(false);
    expect(screen.getByText('Activia Trace')).toBeInTheDocument();
  });

  it('hides the app name when collapsed', () => {
    renderSidebar(true);
    expect(screen.queryByText('Activia Trace')).not.toBeInTheDocument();
  });
});
