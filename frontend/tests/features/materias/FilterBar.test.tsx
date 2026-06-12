import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import FilterBar from '@/features/materias/components/FilterBar';
import type { FilterField } from '@/features/materias/components/FilterBar';

const fields: FilterField[] = [
  {
    key: 'comision',
    label: 'Comision',
    type: 'select',
    options: [
      { value: 'A', label: 'Comision A' },
      { value: 'B', label: 'Comision B' },
    ],
  },
  { key: 'busqueda', label: 'Busqueda', type: 'text', placeholder: 'Buscar...' },
  { key: 'fecha_desde', label: 'Fecha desde', type: 'date' },
  { key: 'minimo', label: 'Minimo', type: 'number', placeholder: '0' },
];

function renderFilterBar(initialEntries = ['/test']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <FilterBar fields={fields} debounceMs={0} />
    </MemoryRouter>,
  );
}

describe('FilterBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all filter fields', () => {
    renderFilterBar();
    expect(screen.getByLabelText('Comision')).toBeInTheDocument();
    expect(screen.getByLabelText('Busqueda')).toBeInTheDocument();
    expect(screen.getByLabelText('Fecha desde')).toBeInTheDocument();
    expect(screen.getByLabelText('Minimo')).toBeInTheDocument();
  });

  it('shows select options', () => {
    renderFilterBar();
    const select = screen.getByLabelText('Comision');
    expect(select).toHaveValue('');
    expect(screen.getByText('Comision A')).toBeInTheDocument();
    expect(screen.getByText('Comision B')).toBeInTheDocument();
  });

  it('does not show clear button when no filters are set', () => {
    renderFilterBar();
    expect(screen.queryByText('Limpiar filtros')).not.toBeInTheDocument();
  });

  it('shows clear button when URL has filters', () => {
    renderFilterBar(['/test?comision=A']);
    expect(screen.getByText('Limpiar filtros')).toBeInTheDocument();
  });

  it('select reflects URL parameter value', () => {
    renderFilterBar(['/test?comision=A']);
    const select = screen.getByLabelText('Comision') as HTMLSelectElement;
    expect(select.value).toBe('A');
  });

  it('text input reflects URL parameter value', () => {
    renderFilterBar(['/test?busqueda=Juan']);
    const input = screen.getByLabelText('Busqueda') as HTMLInputElement;
    expect(input.value).toBe('Juan');
  });
});
