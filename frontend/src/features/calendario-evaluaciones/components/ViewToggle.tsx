import type { ReactNode } from 'react';

// --- Task 4.1: ViewToggle component ---

interface ViewToggleProps {
  view: 'table' | 'calendar';
  onViewChange: (view: 'table' | 'calendar') => void;
}

function ViewToggle({ view, onViewChange }: ViewToggleProps): ReactNode {
  return (
    <div className="inline-flex rounded-md border border-gray-300 overflow-hidden">
      <button
        type="button"
        onClick={() => onViewChange('table')}
        className={`px-4 py-2 text-sm font-medium transition-colors ${
          view === 'table'
            ? 'bg-blue-600 text-white'
            : 'bg-white text-gray-700 hover:bg-gray-50'
        }`}
      >
        Tabla
      </button>
      <button
        type="button"
        onClick={() => onViewChange('calendar')}
        className={`px-4 py-2 text-sm font-medium transition-colors ${
          view === 'calendar'
            ? 'bg-blue-600 text-white'
            : 'bg-white text-gray-700 hover:bg-gray-50'
        }`}
      >
        Calendario
      </button>
    </div>
  );
}

export default ViewToggle;
