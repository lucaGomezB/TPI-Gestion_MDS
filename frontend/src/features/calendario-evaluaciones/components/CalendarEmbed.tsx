import { useState, useCallback, type ReactNode } from 'react';
import Modal from '@/shared/components/Modal';

// --- Task 4.5: CalendarEmbed modal ---

interface CalendarEmbedProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (formato: string) => void;
  embedCode?: string;
  isLoading: boolean;
}

function CalendarEmbed({
  isOpen,
  onClose,
  onGenerate,
  embedCode,
  isLoading,
}: CalendarEmbedProps): ReactNode {
  const [formato, setFormato] = useState<string>('html');
  const [copied, setCopied] = useState(false);

  const handleGenerate = () => {
    setCopied(false);
    onGenerate(formato);
  };

  const handleCopy = useCallback(async () => {
    if (!embedCode) return;
    try {
      await navigator.clipboard.writeText(embedCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = embedCode;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [embedCode]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Generar Embed - Calendario de Evaluaciones"
      size="lg"
    >
      <div className="space-y-5">
        {/* Format selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Formato</label>
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={() => setFormato('html')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                formato === 'html'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              HTML
            </button>
            <button
              type="button"
              onClick={() => setFormato('markdown')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                formato === 'markdown'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              Markdown
            </button>
          </div>
        </div>

        {/* Generate button */}
        <button
          onClick={handleGenerate}
          disabled={isLoading}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Generando...' : 'Generar Embed'}
        </button>

        {/* Embed code preview */}
        {embedCode && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Codigo generado
            </label>
            <textarea
              readOnly
              value={embedCode}
              rows={8}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono bg-gray-50"
            />
            <button
              onClick={handleCopy}
              className="mt-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              {copied ? 'Copiado!' : 'Copiar al portapapeles'}
            </button>
          </div>
        )}
      </div>
    </Modal>
  );
}

export default CalendarEmbed;
