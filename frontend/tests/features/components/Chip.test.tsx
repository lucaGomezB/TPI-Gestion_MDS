import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Chip from '../../../src/shared/components/Chip';

describe('Chip', () => {
  it('renders the label', () => {
    render(< Chip>React</Chip>);
    expect(screen.getByText('React')).toBeInTheDocument();
  });

  it('renders an X icon when onRemove is provided', () => {
    const onRemove = vi.fn();
    render(<Chip onRemove={onRemove}>React</Chip>);
    const removeButton = screen.getByRole('button');
    expect(removeButton).toBeInTheDocument();
  });

  it('calls onRemove when X icon is clicked', () => {
    const onRemove = vi.fn();
    render(<Chip onRemove={onRemove}>React</Chip>);
    fireEvent.click(screen.getByRole('button'));
    expect(onRemove).toHaveBeenCalledTimes(1);
  });

  it('does not render a remove button when onRemove is not provided', () => {
    render(<Chip>React</Chip>);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('merges custom className', () => {
    render(<Chip className="custom-chip">React</Chip>);
    const chip = screen.getByText('React');
    expect(chip.className).toContain('custom-chip');
  });

  it('renders with tertiary/10 background', () => {
    render(<Chip>React</Chip>);
    const chip = screen.getByText('React');
    expect(chip.className).toContain('bg-tertiary/10');
  });
});
