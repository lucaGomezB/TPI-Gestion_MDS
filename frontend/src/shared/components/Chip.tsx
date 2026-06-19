import type { ReactNode } from 'react';

interface ChipProps {
  children: ReactNode;
  onRemove?: () => void;
  className?: string;
}

function Chip({ children, onRemove, className = '' }: ChipProps): ReactNode {
  return (
    <span
      className={`inline-flex items-center gap-1 bg-tertiary/10 text-secondary text-label-sm rounded px-3 py-1 ${className}`}
    >
      {children}
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="inline-flex items-center justify-center w-3.5 h-3.5 ml-0.5 rounded-full hover:bg-tertiary/20 transition-colors"
          aria-label="Eliminar"
        >
          <svg
            className="w-2.5 h-2.5"
            viewBox="0 0 10 10"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            aria-hidden="true"
          >
            <path d="M1 1L9 9M9 1L1 9" />
          </svg>
        </button>
      )}
    </span>
  );
}

export { Chip };
export default Chip;
