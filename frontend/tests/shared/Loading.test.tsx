import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Loading from '../../src/shared/components/Loading';

describe('Loading', () => {
  it('renders a spinner/skeleton by default', () => {
    render(<Loading />);
    const element = screen.getByRole('status');
    expect(element).toBeInTheDocument();
  });

  it('renders an optional message when provided', () => {
    render(<Loading message="Cargando usuarios..." />);
    expect(screen.getByText('Cargando usuarios...')).toBeInTheDocument();
  });

  it('renders a full-page variant when fullPage is true', () => {
    render(<Loading fullPage />);
    const container = screen.getByRole('status');
    expect(container).toHaveClass('min-h-screen');
  });

  it('renders without message when message is not provided', () => {
    render(<Loading />);
    expect(screen.queryByText(/./)).not.toBeInTheDocument();
  });

  it('renders a skeleton variant when skeleton is true', () => {
    render(<Loading skeleton />);
    expect(screen.getByTestId('skeleton-rows')).toBeInTheDocument();
  });
});
