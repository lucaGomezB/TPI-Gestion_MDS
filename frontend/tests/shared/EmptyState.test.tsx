import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import EmptyState from '../../src/shared/components/EmptyState';

describe('EmptyState', () => {
  it('renders a title', () => {
    render(<EmptyState title="No hay resultados" />);
    expect(screen.getByText('No hay resultados')).toBeInTheDocument();
  });

  it('renders a description when provided', () => {
    render(<EmptyState title="Sin datos" description="No se encontraron registros para esta búsqueda." />);
    expect(screen.getByText('No se encontraron registros para esta búsqueda.')).toBeInTheDocument();
  });

  it('renders an action button when actionLabel and onAction are provided', () => {
    const onAction = vi.fn();
    render(<EmptyState title="Vacío" actionLabel="Crear nuevo" onAction={onAction} />);
    const button = screen.getByRole('button', { name: /crear nuevo/i });
    expect(button).toBeInTheDocument();
  });

  it('calls onAction when action button is clicked', () => {
    const onAction = vi.fn();
    render(<EmptyState title="Vacío" actionLabel="Crear" onAction={onAction} />);
    fireEvent.click(screen.getByRole('button', { name: /crear/i }));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it('renders without description when not provided', () => {
    render(<EmptyState title="Solo título" />);
    expect(screen.getByText('Solo título')).toBeInTheDocument();
  });

  it('renders an icon by default', () => {
    render(<EmptyState title="Vacío" />);
    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });
});
