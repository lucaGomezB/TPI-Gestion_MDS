import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import RedirectPage from '../../src/shared/components/RedirectPage';

function renderWithRouter(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('RedirectPage', () => {
  it('renders title and description', () => {
    renderWithRouter(
      <RedirectPage
        title="Seccion en construccion"
        description="Esta funcionalidad esta disponible desde otras paginas."
        links={[]}
      />,
    );

    expect(screen.getByText('Seccion en construccion')).toBeInTheDocument();
    expect(
      screen.getByText('Esta funcionalidad esta disponible desde otras paginas.'),
    ).toBeInTheDocument();
  });

  it('renders link buttons pointing to the correct paths', () => {
    renderWithRouter(
      <RedirectPage
        title="Alumnos"
        description="Gestione alumnos desde cada materia."
        links={[
          { label: 'Ir a Materias', path: '/materias' },
          { label: 'Ir a Mis Equipos', path: '/mis-equipos' },
        ]}
      />,
    );

    const materiasLink = screen.getByRole('link', { name: /ir a materias/i });
    const equiposLink = screen.getByRole('link', { name: /ir a mis equipos/i });

    expect(materiasLink).toBeInTheDocument();
    expect(materiasLink).toHaveAttribute('href', '/materias');

    expect(equiposLink).toBeInTheDocument();
    expect(equiposLink).toHaveAttribute('href', '/mis-equipos');
  });

  it('renders a single link correctly', () => {
    renderWithRouter(
      <RedirectPage
        title="Un solo destino"
        description="Solo hay una pagina relevante."
        links={[{ label: 'Ir a Materias', path: '/materias' }]}
      />,
    );

    const link = screen.getByRole('link', { name: /ir a materias/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/materias');
  });

  it('renders an SVG icon', () => {
    renderWithRouter(
      <RedirectPage
        title="Con icono"
        description="Debe mostrar un icono."
        links={[]}
      />,
    );

    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('renders no links when links array is empty', () => {
    renderWithRouter(
      <RedirectPage
        title="Sin enlaces"
        description="No hay paginas destino."
        links={[]}
      />,
    );

    const links = screen.queryAllByRole('link');
    expect(links).toHaveLength(0);
  });
});
