import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#0F172A',
        secondary: '#334155',
        tertiary: '#64748B',
        background: '#F8FAFC',
        'on-background': '#191C1E',
        'on-surface': '#191C1E',
        'on-surface-variant': '#45464D',
        surface: '#FFFFFF',
        'surface-dim': '#D8DADC',
        'surface-bright': '#F7F9FB',
        'surface-container': '#ECEEF0',
        'surface-container-high': '#E6E8EA',
        'surface-container-highest': '#E0E3E5',
        'on-primary': '#FFFFFF',
        'on-secondary': '#FFFFFF',
        'on-tertiary': '#FFFFFF',
        'primary-container': '#131B2E',
        'secondary-container': '#D5E3FD',
        error: '#BA1A1A',
        'on-error': '#FFFFFF',
        'error-container': '#FFDAD6',
      },
      fontFamily: {
        serif: ['"Source Serif 4"', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'headline-lg': ['40px', { lineHeight: '48px', fontWeight: '600', letterSpacing: '-0.02em' }],
        'headline-lg-mobile': ['30px', { lineHeight: '36px', fontWeight: '600', letterSpacing: '-0.01em' }],
        'headline-md': ['28px', { lineHeight: '36px', fontWeight: '500' }],
        'headline-sm': ['20px', { lineHeight: '28px', fontWeight: '500' }],
        'body-lg': ['18px', { lineHeight: '28px', fontWeight: '400' }],
        'body-md': ['16px', { lineHeight: '24px', fontWeight: '400' }],
        'body-sm': ['14px', { lineHeight: '20px', fontWeight: '400' }],
        'label-md': ['14px', { lineHeight: '16px', fontWeight: '600', letterSpacing: '0.02em' }],
        'label-sm': ['12px', { lineHeight: '16px', fontWeight: '500', letterSpacing: '0.04em' }],
      },
      borderRadius: {
        sm: '0.125rem',
        DEFAULT: '0.25rem',
        md: '0.375rem',
        lg: '0.5rem',
        xl: '0.75rem',
      },
      boxShadow: {
        card: '0px 4px 20px rgba(15, 23, 42, 0.04)',
        'card-active': '0px 8px 30px rgba(15, 23, 42, 0.08)',
      },
      maxWidth: {
        container: '1280px',
      },
      spacing: {
        gutter: '24px',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
} satisfies Config;
