import type { ReactNode } from 'react';

interface BadgeProps {
  variant?: 'success' | 'warning' | 'error' | 'info' | 'neutral';
  children: ReactNode;
  className?: string;
}

const variantConfig: Record<
  string,
  { badge: string; dot: string }
> = {
  success: {
    badge: 'bg-green-50 text-green-800',
    dot: 'bg-green-500',
  },
  warning: {
    badge: 'bg-yellow-50 text-yellow-800',
    dot: 'bg-yellow-500',
  },
  error: {
    badge: 'bg-red-50 text-red-800',
    dot: 'bg-red-500',
  },
  info: {
    badge: 'bg-blue-50 text-blue-800',
    dot: 'bg-blue-500',
  },
  neutral: {
    badge: 'bg-slate-100 text-slate-700',
    dot: 'bg-slate-500',
  },
};

function Badge({
  variant = 'neutral',
  children,
  className = '',
}: BadgeProps): ReactNode {
  const config = variantConfig[variant];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-label-sm ${config.badge} ${className}`}
    >
      <span
        className={`inline-block w-1.5 h-1.5 rounded-full ${config.dot}`}
        aria-hidden="true"
      />
      {children}
    </span>
  );
}

export { Badge };
export default Badge;
