import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import CompletionReportImport from '@/features/materias/components/CompletionReportImport';

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('CompletionReportImport', () => {
  const defaultProps = {
    materiaId: 'm1',
    onUpload: vi.fn(),
    onExport: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders upload interface', () => {
    render(<CompletionReportImport {...defaultProps} />, { wrapper: createWrapper() });
    expect(screen.getByText('Reporte de completitud')).toBeInTheDocument();
    expect(screen.getByText(/Click para seleccionar/)).toBeInTheDocument();
  });

  it('shows file format info', () => {
    render(<CompletionReportImport {...defaultProps} />, { wrapper: createWrapper() });
    expect(screen.getByText(/\.xlsx/)).toBeInTheDocument();
    expect(screen.getByText(/10MB/)).toBeInTheDocument();
  });
});
