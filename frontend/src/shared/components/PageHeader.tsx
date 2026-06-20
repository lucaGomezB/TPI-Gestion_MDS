import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface Breadcrumb {
  label: string;
  href?: string;
}

interface Action {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
}

interface PageHeaderProps {
  title: string;
  breadcrumbs?: Breadcrumb[];
  actions?: Action[];
}

function PageHeader({ title, breadcrumbs, actions }: PageHeaderProps): ReactNode {
  return (
    <div className="mb-6">
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="flex items-center space-x-2 text-sm text-[#64748B] mb-2" aria-label="Breadcrumb">
          {breadcrumbs.map((crumb, index) => (
            <span key={index} className="flex items-center">
              {index > 0 && <span className="mx-2 text-[#64748B]/30">/</span>}
              {crumb.href ? (
                <Link to={crumb.href} className="hover:text-[#334155] transition-colors">
                  {crumb.label}
                </Link>
              ) : (
                <span className="text-[#334155] font-medium">{crumb.label}</span>
              )}
            </span>
          ))}
        </nav>
      )}
      <div className="flex items-center justify-between">
        <h1 className="font-serif text-3xl lg:text-4xl text-[#0F172A]">{title}</h1>
        {actions && actions.length > 0 && (
          <div className="flex items-center space-x-3">
            {actions.map((action, index) => (
              <button
                key={index}
                onClick={action.onClick}
                className={
                  action.variant === 'secondary'
                    ? 'px-4 py-2 text-sm font-medium text-[#334155] bg-white border border-[#64748B] rounded-md hover:bg-[#F8FAFC] transition-colors'
                    : 'px-4 py-2 text-sm font-medium text-white bg-[#0F172A] rounded-md hover:bg-[#0F172A]/90 transition-colors'
                }
              >
                {action.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default PageHeader;
