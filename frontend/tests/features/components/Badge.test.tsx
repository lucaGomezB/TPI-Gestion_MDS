import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Badge from '../../../src/shared/components/Badge';

describe('Badge', () => {
  it('renders the text', () => {
    render(<Badge>Active</Badge>);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('renders a colored dot indicator', () => {
    const { container } = render(<Badge>Active</Badge>);
    const dot = container.querySelector('span.rounded-full');
    expect(dot).toBeInTheDocument();
  });

  it('applies success variant styles', () => {
    const { container } = render(<Badge variant="success">Ok</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('bg-green-50');
    const dot = container.querySelector('span.rounded-full');
    expect(dot?.className).toContain('bg-green-500');
  });

  it('applies warning variant styles', () => {
    const { container } = render(<Badge variant="warning">Warning</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('bg-yellow-50');
  });

  it('applies error variant styles', () => {
    const { container } = render(<Badge variant="error">Error</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('bg-red-50');
  });

  it('applies info variant styles', () => {
    const { container } = render(<Badge variant="info">Info</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('bg-blue-50');
  });

  it('applies neutral variant styles by default', () => {
    const { container } = render(<Badge>Default</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('bg-slate-100');
  });

  it('merges custom className', () => {
    render(<Badge className="custom-badge">Styled</Badge>);
    const badge = screen.getByText('Styled');
    expect(badge.className).toContain('custom-badge');
  });
});
