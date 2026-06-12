import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ErrorDisplay from '../../src/shared/components/ErrorDisplay';

describe('ErrorDisplay', () => {
  it('renders an error message', () => {
    render(<ErrorDisplay message="Ocurrió un error" />);
    expect(screen.getByText('Ocurrió un error')).toBeInTheDocument();
  });

  it('renders a retry button when onRetry is provided', () => {
    const onRetry = vi.fn();
    render(<ErrorDisplay message="Error" onRetry={onRetry} />);
    const button = screen.getByRole('button', { name: /reintentar/i });
    expect(button).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', () => {
    const onRetry = vi.fn();
    render(<ErrorDisplay message="Error" onRetry={onRetry} />);
    fireEvent.click(screen.getByRole('button', { name: /reintentar/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('does not render retry button when onRetry is not provided', () => {
    render(<ErrorDisplay message="Error" />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('renders with fullPage variant', () => {
    render(<ErrorDisplay message="Error crítico" fullPage />);
    const container = screen.getByRole('alert');
    expect(container).toHaveClass('min-h-screen');
  });

  it('renders default error message when message is not provided', () => {
    render(<ErrorDisplay />);
    expect(screen.getByText(/ocurrió un error/i)).toBeInTheDocument();
  });
});
