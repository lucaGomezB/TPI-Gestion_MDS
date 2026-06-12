import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import TwoFactorPage from '../../src/features/auth/pages/TwoFactorPage';

describe('TwoFactorPage', () => {
  it('renders the TOTP code input form', () => {
    render(
      <BrowserRouter>
        <TwoFactorPage />
      </BrowserRouter>,
    );
    const heading = screen.getByRole('heading', { name: /verificación en dos pasos/i });
    expect(heading).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /verificar|confirmar/i })).toBeInTheDocument();
  });

  it('renders a link back to login', () => {
    render(
      <BrowserRouter>
        <TwoFactorPage />
      </BrowserRouter>,
    );
    const loginLink = screen.getByRole('link', { name: /volver|login|iniciar sesión/i });
    expect(loginLink).toBeInTheDocument();
    expect(loginLink).toHaveAttribute('href', '/login');
  });

  it('renders the code input field', () => {
    render(
      <BrowserRouter>
        <TwoFactorPage />
      </BrowserRouter>,
    );
    const input = screen.getByRole('textbox');
    expect(input).toBeInTheDocument();
  });
});
