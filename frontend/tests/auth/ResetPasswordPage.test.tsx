import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import ResetPasswordPage from '../../src/features/auth/pages/ResetPasswordPage';

describe('ResetPasswordPage', () => {
  it('renders the reset password form with password fields', () => {
    render(
      <BrowserRouter>
        <ResetPasswordPage />
      </BrowserRouter>,
    );
    expect(screen.getByLabelText(/nueva contraseña|contraseña nueva/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirmar|repetir/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /restablecer|cambiar|guardar/i })).toBeInTheDocument();
  });

  it('shows validation error when passwords do not match', async () => {
    render(
      <BrowserRouter>
        <ResetPasswordPage />
      </BrowserRouter>,
    );

    const passwordInput = screen.getByLabelText(/nueva contraseña|contraseña nueva/i);
    const confirmInput = screen.getByLabelText(/confirmar|repetir/i);

    fireEvent.change(passwordInput, { target: { value: 'Password1!' } });
    fireEvent.change(confirmInput, { target: { value: 'DifferentPassword1!' } });
    fireEvent.click(screen.getByRole('button', { name: /restablecer|cambiar|guardar/i }));

    await waitFor(() => {
      expect(screen.getByText(/no coinciden|diferentes/i)).toBeInTheDocument();
    });
  });
});
