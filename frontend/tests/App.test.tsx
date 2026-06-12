import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import App from '../src/App';

describe('App', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders without crashing', () => {
    render(<App />);
    // Should at least render something
    expect(document.body.querySelector('div')).toBeInTheDocument();
  });

  it('renders login page at /login route', async () => {
    window.history.pushState({}, '', '/login');
    render(<App />);
    const loginButton = await screen.findByRole('button', { name: /ingresar/i }, { timeout: 3000 });
    expect(loginButton).toBeInTheDocument();
  });
});
