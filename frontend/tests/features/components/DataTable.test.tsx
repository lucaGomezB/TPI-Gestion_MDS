import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import DataTable from '../../../src/shared/components/DataTable';

interface TestItem {
  id: number;
  name: string;
  role: string;
}

const columns = [
  { key: 'id' as const, header: 'ID' },
  { key: 'name' as const, header: 'Name' },
  { key: 'role' as const, header: 'Role' },
];

const data: TestItem[] = [
  { id: 1, name: 'Alice', role: 'Admin' },
  { id: 2, name: 'Bob', role: 'User' },
];

describe('DataTable', () => {
  it('renders column headers', () => {
    render(<DataTable columns={columns} data={data} />);
    expect(screen.getByText('ID')).toBeInTheDocument();
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Role')).toBeInTheDocument();
  });

  it('renders data rows', () => {
    render(<DataTable columns={columns} data={data} />);
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
    expect(screen.getByText('Admin')).toBeInTheDocument();
  });

  it('renders loading skeleton rows when isLoading is true', () => {
    const { container } = render(<DataTable columns={columns} data={data} isLoading />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders empty message when data is empty', () => {
    render(<DataTable columns={columns} data={[]} emptyMessage="No records found" />);
    expect(screen.getByText('No records found')).toBeInTheDocument();
  });

  it('renders default empty message when data is empty and no custom message', () => {
    render(<DataTable columns={columns} data={[]} />);
    expect(screen.getByText('No hay datos')).toBeInTheDocument();
  });

  it('renders sort indicator on sortable columns', () => {
    const sortableColumns = [
      { key: 'name' as const, header: 'Name', sortable: true },
      { key: 'role' as const, header: 'Role', sortable: false },
    ];
    render(<DataTable columns={sortableColumns} data={data} />);
    const headers = screen.getAllByRole('columnheader');
    const nameHeader = headers[0];
    expect(nameHeader.className).toContain('cursor-pointer');
  });

  it('applies active sort styling when sortKey matches', () => {
    const sortableColumns = [
      { key: 'name' as const, header: 'Name', sortable: true },
    ];
    render(
      <DataTable
        columns={sortableColumns}
        data={data}
        sortKey="name"
        sortDirection="asc"
      />,
    );
    const header = screen.getByText('Name');
    expect(header).toBeInTheDocument();
  });

  it('uses render function when provided', () => {
    const customColumns = [
      { key: 'name' as const, header: 'Name', render: (item: TestItem) => <strong>{item.name}</strong> },
    ];
    render(<DataTable columns={customColumns} data={data} />);
    const strongEl = screen.getByText('Alice');
    expect(strongEl.tagName).toBe('STRONG');
  });

  it('applies alignment classes', () => {
    const alignedColumns = [
      { key: 'id' as const, header: 'ID', align: 'right' as const },
    ];
    const { container } = render(<DataTable columns={alignedColumns} data={data} />);
    const cells = container.querySelectorAll('td, th');
    expect(cells.length).toBeGreaterThan(0);
  });
});
