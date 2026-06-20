import type { ReactNode } from 'react';

interface CardProps {
  header?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
  className?: string;
}

function Card({ header, footer, children, className = '' }: CardProps): ReactNode {
  return (
    <div
      className={`bg-white rounded-lg border border-tertiary/20 shadow-card ${className}`}
    >
      {header && (
        <div className="px-6 py-4 border-b border-tertiary/10">
          {header}
        </div>
      )}
      <div className="p-6">{children}</div>
      {footer && (
        <div className="px-6 py-4 border-t border-tertiary/10">
          {footer}
        </div>
      )}
    </div>
  );
}

export { Card };
export default Card;
