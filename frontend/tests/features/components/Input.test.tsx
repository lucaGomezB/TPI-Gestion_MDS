import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Input from '../../../src/shared/components/Input';

describe('Input', () => {
  it('renders a label', () => {
    render(<Input label="Email" />);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
  });

  it('renders an input element', () => {
    render(<Input label="Name" />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('applies error state styles when error is provided', () => {
    render(<Input label="Email" error="Email is required" />);
    const input = screen.getByRole('textbox');
    expect(input.className).toContain('border-error');
    expect(screen.getByText('Email is required')).toBeInTheDocument();
  });

  it('does not show error message when error is not provided', () => {
    render(<Input label="Name" />);
    expect(screen.queryByText('Email is required')).not.toBeInTheDocument();
  });

  it('handles onChange event', () => {
    const onChange = vi.fn();
    render(<Input label="Name" onChange={onChange} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'John' } });
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it('renders with placeholder', () => {
    render(<Input label="Name" placeholder="Enter your name" />);
    expect(screen.getByPlaceholderText('Enter your name')).toBeInTheDocument();
  });

  it('merges custom className', () => {
    render(<Input label="Name" className="custom-class" />);
    expect(screen.getByRole('textbox').className).toContain('custom-class');
  });

  it('forwards ref', () => {
    const ref = vi.fn();
    render(<Input label="Name" ref={ref} />);
    expect(ref).toHaveBeenCalled();
  });

  it('associates label with input via htmlFor', () => {
    render(<Input label="Email" id="email-field" />);
    const label = screen.getByText('Email');
    expect(label.getAttribute('for')).toBe('email-field');
  });
});
