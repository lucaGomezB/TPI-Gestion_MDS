import { useState, type ReactNode } from 'react';

interface CsvExportButtonProps {
  onExport: () => Promise<void>;
  label?: string;
}

function CsvExportButton({ onExport, label = 'Exportar CSV' }: CsvExportButtonProps): ReactNode {
  const [exporting, setExporting] = useState(false);

  const handleClick = async () => {
    setExporting(true);
    try {
      await onExport();
    } catch {
      // Error handling is done by the caller
    } finally {
      setExporting(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={exporting}
      className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
    >
      {exporting ? (
        <>
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Exportando...
        </>
      ) : (
        label
      )}
    </button>
  );
}

export default CsvExportButton;
