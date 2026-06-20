import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Card from '../../../src/shared/components/Card';

describe('Card', () => {
  it('renders children', () => {
    render(<Card><p>Card content</p></Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('renders header when provided', () => {
    render(<Card header={<h2>Card Header</h2>}><p>Body</p></Card>);
    expect(screen.getByText('Card Header')).toBeInTheDocument();
  });

  it('renders footer when provided', () => {
    render(<Card footer={<div>Footer</div>}><p>Body</p></Card>);
    expect(screen.getByText('Footer')).toBeInTheDocument();
  });

  it('does not render header section when header is not provided', () => {
    const { container } = render(<Card><p>Body</p></Card>);
    const dividers = container.querySelectorAll('.border-b');
    expect(dividers.length).toBe(0);
  });

  it('does not render footer section when footer is not provided', () => {
    const { container } = render(<Card><p>Body</p></Card>);
    const dividers = container.querySelectorAll('.border-t');
    expect(dividers.length).toBe(0);
  });

  it('applies custom className', () => {
    const { container } = render(<Card className="custom-class"><p>Content</p></Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('custom-class');
  });

  it('renders shadow-card by default', () => {
    const { container } = render(<Card><p>Content</p></Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('shadow-card');
  });
});
