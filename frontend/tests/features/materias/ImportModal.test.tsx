import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ImportModal from '@/features/materias/components/ImportModal';

describe('ImportModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onUpload: vi.fn<[File], Promise<{ actividad: string; filas: number; seleccionada: boolean }[]>>(),
    onConfirm: vi.fn<[string[]], Promise<void>>(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when closed', () => {
    const { container } = render(<ImportModal {...defaultProps} isOpen={false} />);
    expect(container.innerHTML).toBe('');
  });

  it('renders upload interface when open', () => {
    render(<ImportModal {...defaultProps} />);
    expect(screen.getByText('Importar calificaciones')).toBeInTheDocument();
    expect(screen.getByText(/Click para seleccionar/)).toBeInTheDocument();
  });

  it('shows file format info', () => {
    render(<ImportModal {...defaultProps} />);
    expect(screen.getByText(/\.xlsx/)).toBeInTheDocument();
    expect(screen.getByText(/10MB/)).toBeInTheDocument();
  });

  it('calls onClose when clicking the close button', () => {
    render(<ImportModal {...defaultProps} />);
    const closeButton = screen.getByLabelText('Cerrar');
    fireEvent.click(closeButton);
    expect(defaultProps.onClose).toHaveBeenCalled();
  });
});
