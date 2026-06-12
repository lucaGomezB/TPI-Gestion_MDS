import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import PageHeader from '../../src/shared/components/PageHeader';

function renderWithRouter(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('PageHeader', () => {
  it('renders the title', () => {
    renderWithRouter(<PageHeader title="Usuarios" />);
    expect(screen.getByText('Usuarios')).toBeInTheDocument();
  });

  it('renders breadcrumbs when provided', () => {
    renderWithRouter(
      <PageHeader
        title="Editar Usuario"
        breadcrumbs={[
          { label: 'Inicio', href: '/' },
          { label: 'Usuarios', href: '/usuarios' },
          { label: 'Editar' },
        ]}
      />,
    );
    expect(screen.getByText('Inicio')).toBeInTheDocument();
    expect(screen.getByText('Usuarios')).toBeInTheDocument();
    expect(screen.getByText('Editar')).toBeInTheDocument();
  });

  it('renders action buttons when actions are provided', () => {
    const onClick = vi.fn();
    renderWithRouter(
      <PageHeader
        title="Usuarios"
        actions={[
          { label: 'Nuevo', onClick },
        ]}
      />,
    );
    expect(screen.getByRole('button', { name: /nuevo/i })).toBeInTheDocument();
  });

  it('renders breadcrumb links with correct hrefs', () => {
    renderWithRouter(
      <PageHeader
        title="Page"
        breadcrumbs={[
          { label: 'Home', href: '/home' },
          { label: 'Current' },
        ]}
      />,
    );
    const link = screen.getByText('Home').closest('a');
    expect(link).toHaveAttribute('href', '/home');
  });

  it('renders without breadcrumbs when not provided', () => {
    renderWithRouter(<PageHeader title="Solo título" />);
    expect(screen.getByText('Solo título')).toBeInTheDocument();
  });
});
