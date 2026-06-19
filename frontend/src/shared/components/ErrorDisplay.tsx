import type { ReactNode } from 'react';

interface ErrorDisplayProps {
  message?: string;
  onRetry?: () => void;
  fullPage?: boolean;
}

function ErrorDisplay({ message, onRetry, fullPage = false }: ErrorDisplayProps): ReactNode {
  const displayMessage = message || 'Ocurrió un error inesperado.';

  if (fullPage) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50" role="alert">
        <div className="flex flex-col items-center justify-center space-y-4 p-8 text-center">
          <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
            <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
          </div>
          <p className="text-base text-[#64748B]">{displayMessage}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 transition-colors"
            >
              Reintentar
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center space-y-4 p-8 text-center" role="alert">
      <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
        <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
      </div>
      <p className="text-base text-[#64748B]">{displayMessage}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 transition-colors"
        >
          Reintentar
        </button>
      )}
    </div>
  );
}

export default ErrorDisplay;
