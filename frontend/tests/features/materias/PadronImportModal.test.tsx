import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PadronImportModal from '@/features/materias/components/PadronImportModal';

describe('PadronImportModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onUpload: vi.fn(),
    onReplace: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when closed', () => {
    const { container } = render(<PadronImportModal {...defaultProps} isOpen={false} />);
    expect(container.innerHTML).toBe('');
  });

  it('renders upload interface when open', () => {
    render(<PadronImportModal {...defaultProps} />);
    expect(screen.getByText('Importar padron')).toBeInTheDocument();
    expect(screen.getByText(/Click para seleccionar/)).toBeInTheDocument();
  });

  it('shows mode selection buttons', () => {
    render(<PadronImportModal {...defaultProps} />);
    expect(screen.getByText('Agregar nuevos')).toBeInTheDocument();
    expect(screen.getByText('Reemplazar todo')).toBeInTheDocument();
  });

  it('calls onClose when clicking the close button', () => {
    render(<PadronImportModal {...defaultProps} />);
    const closeButton = screen.getByLabelText('Cerrar');
    fireEvent.click(closeButton);
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('renders file format info', () => {
    render(<PadronImportModal {...defaultProps} />);
    expect(screen.getByText(/DNI/)).toBeInTheDocument();
    expect(screen.getByText(/10MB/)).toBeInTheDocument();
  });
});
