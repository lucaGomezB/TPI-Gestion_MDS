import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import DataTable from '../../../src/features/estructura-academica/components/DataTable';
import type { Column } from '../../../src/features/estructura-academica/components/DataTable';

interface TestItem {
  id: string;
  name: string;
  code: string;
  active: boolean;
}

const columns: Column<TestItem>[] = [
  { key: 'code', header: 'Código' },
  { key: 'name', header: 'Nombre' },
];

const data: TestItem[] = [
  { id: '1', name: 'Item 1', code: 'ITM-01', active: true },
  { id: '2', name: 'Item 2', code: 'ITM-02', active: false },
];

describe('DataTable', () => {
  it('renders headers and data rows', () => {
    render(
      <DataTable<TestItem>
        columns={columns}
        data={data}
        keyExtractor={(item) => item.id}
      />,
    );

    expect(screen.getByText('Código')).toBeInTheDocument();
    expect(screen.getByText('Nombre')).toBeInTheDocument();
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('ITM-02')).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    const onEdit = vi.fn();
    render(
      <DataTable<TestItem>
        columns={columns}
        data={data}
        keyExtractor={(item) => item.id}
        onEdit={onEdit}
      />,
    );

    const editButtons = screen.getAllByText('Editar');
    fireEvent.click(editButtons[0]);
    expect(onEdit).toHaveBeenCalledWith(data[0]);
  });

  it('renders toggle buttons with correct labels', () => {
    render(
      <DataTable<TestItem>
        columns={columns}
        data={data}
        keyExtractor={(item) => item.id}
        onToggle={() => {}}
        toggleLabel={(item) => (item.active ? 'Activa' : 'Inactiva')}
        toggleActive={(item) => item.active}
      />,
    );

    expect(screen.getByText('Activa')).toBeInTheDocument();
    expect(screen.getByText('Inactiva')).toBeInTheDocument();
  });

  it('calls onToggle when toggle button is clicked', () => {
    const onToggle = vi.fn();
    render(
      <DataTable<TestItem>
        columns={columns}
        data={data}
        keyExtractor={(item) => item.id}
        onToggle={onToggle}
        toggleLabel={(item) => (item.active ? 'Activa' : 'Inactiva')}
        toggleActive={(item) => item.active}
      />,
    );

    const toggleButtons = screen.getAllByText('Activa');
    fireEvent.click(toggleButtons[0]);
    expect(onToggle).toHaveBeenCalledWith(data[0]);
  });

  it('renders empty state when data is empty', () => {
    const { container } = render(
      <DataTable<TestItem>
        columns={columns}
        data={[]}
        keyExtractor={(item) => item.id}
      />,
    );

    const tbody = container.querySelector('tbody');
    expect(tbody?.children.length).toBe(0);
  });
});
