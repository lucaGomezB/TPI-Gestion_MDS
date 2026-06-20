import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import App from '../src/App';

const mockUser = {
  id: '1',
  email: 'admin@test.com',
  nombre: 'Admin',
  apellidos: 'Test',
  rol: 'ADMIN',
  tenant_id: 'tenant-1',
};

function setupAuth() {
  localStorage.setItem('access_token', 'fake-token');
  localStorage.setItem('refresh_token', 'fake-refresh');
  localStorage.setItem('user', JSON.stringify(mockUser));
}

describe('App', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders without crashing', () => {
    render(<App />);
    expect(document.body.querySelector('div')).toBeInTheDocument();
  });

  it('renders login page at /login route', async () => {
    window.history.pushState({}, '', '/login');
    render(<App />);
    const loginButton = await screen.findByRole('button', { name: /ingresar/i }, { timeout: 3000 });
    expect(loginButton).toBeInTheDocument();
  });

  describe('redirect pages for protected routes', () => {
    beforeEach(() => {
      setupAuth();
    });

    it('renders redirect page at /alumnos with links to Materias and Mis Equipos', async () => {
      window.history.pushState({}, '', '/alumnos');
      render(<App />);

      const linkMaterias = await screen.findByRole('link', { name: /ir a materias/i }, { timeout: 5000 });
      const linkEquipos = await screen.findByRole('link', { name: /ir a mis equipos/i }, { timeout: 5000 });

      expect(linkMaterias).toBeInTheDocument();
      expect(linkMaterias).toHaveAttribute('href', '/materias');
      expect(linkEquipos).toBeInTheDocument();
      expect(linkEquipos).toHaveAttribute('href', '/mis-equipos');
    });

    it('renders redirect page at /comisiones with links to Materias and Asignaciones', async () => {
      window.history.pushState({}, '', '/comisiones');
      render(<App />);

      const linkMaterias = await screen.findByRole('link', { name: /ir a materias/i }, { timeout: 5000 });
      const linkAsignaciones = await screen.findByRole('link', { name: /ir a asignaciones/i }, { timeout: 5000 });

      expect(linkMaterias).toBeInTheDocument();
      expect(linkMaterias).toHaveAttribute('href', '/materias');
      expect(linkAsignaciones).toBeInTheDocument();
      expect(linkAsignaciones).toHaveAttribute('href', '/admin/equipos/asignaciones');
    });

    it('renders redirect page at /calificaciones with link to Materias', async () => {
      window.history.pushState({}, '', '/calificaciones');
      render(<App />);

      const linkMaterias = await screen.findByRole('link', { name: /ir a materias/i }, { timeout: 5000 });
      expect(linkMaterias).toBeInTheDocument();
      expect(linkMaterias).toHaveAttribute('href', '/materias');
    });

    it('renders redirect page at /roles', async () => {
      window.history.pushState({}, '', '/roles');
      render(<App />);

      const heading = await screen.findByRole('heading', { name: 'Roles', level: 3 }, { timeout: 5000 });
      expect(heading).toBeInTheDocument();
    });

    it('renders redirect page at /tareas-internas', async () => {
      window.history.pushState({}, '', '/tareas-internas');
      render(<App />);

      const heading = await screen.findByRole('heading', { name: 'Tareas Internas', level: 3 }, { timeout: 5000 });
      expect(heading).toBeInTheDocument();
    });
  });
});
