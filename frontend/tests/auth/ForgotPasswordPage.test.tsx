import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import ForgotPasswordPage from '../../src/features/auth/pages/ForgotPasswordPage';

describe('ForgotPasswordPage', () => {
  it('renders the forgot password form with email field', () => {
    render(
      <BrowserRouter>
        <ForgotPasswordPage />
      </BrowserRouter>,
    );
    expect(screen.getByLabelText(/correo electrónico|email/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /enviar|restablecer|recuperar/i })).toBeInTheDocument();
  });

  it('renders a link back to login', () => {
    render(
      <BrowserRouter>
        <ForgotPasswordPage />
      </BrowserRouter>,
    );
    const loginLink = screen.getByRole('link', { name: /volver|login|iniciar sesión/i });
    expect(loginLink).toBeInTheDocument();
    expect(loginLink).toHaveAttribute('href', '/login');
  });

  it('shows success message after submitting valid email', async () => {
    render(
      <BrowserRouter>
        <ForgotPasswordPage />
      </BrowserRouter>,
    );

    const emailInput = screen.getByLabelText(/correo electrónico|email/i);
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /enviar|restablecer|recuperar/i }));

    await waitFor(() => {
      expect(screen.getByText('Correo Enviado')).toBeInTheDocument();
    });
  });
});
