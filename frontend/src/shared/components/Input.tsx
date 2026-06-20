import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', id, ...props }, ref): ReactNode => {
    const inputId = id || label.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="flex flex-col gap-1">
        <label
          htmlFor={inputId}
          className="text-label-md text-secondary"
        >
          {label}
        </label>
        <input
          ref={ref}
          id={inputId}
          className={`border rounded px-4 py-3 text-body-md bg-white transition-colors
            ${error ? 'border-error ring-2 ring-error/20' : 'border-tertiary/30 focus:ring-2 focus:ring-primary/20 focus:border-primary'}
            ${className}`}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={error ? `${inputId}-error` : undefined}
          {...props}
        />
        {error && (
          <p id={`${inputId}-error`} className="text-body-sm text-error" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  },
);

Input.displayName = 'Input';

export { Input };
export default Input;
