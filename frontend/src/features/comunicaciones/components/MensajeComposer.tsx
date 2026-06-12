import { useState, type ReactNode } from 'react';

interface MensajeComposerProps {
  onSend: (contenido: string) => void;
  isSubmitting?: boolean;
  placeholder?: string;
}

function MensajeComposer({
  onSend,
  isSubmitting = false,
  placeholder = 'Escriba su mensaje...',
}: MensajeComposerProps): ReactNode {
  const [contenido, setContenido] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (contenido.trim() && !isSubmitting) {
      onSend(contenido.trim());
      setContenido('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2">
      <div className="flex-1">
        <textarea
          value={contenido}
          onChange={(e) => setContenido(e.target.value)}
          rows={2}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm resize-none"
          placeholder={placeholder}
        />
      </div>
      <button
        type="submit"
        disabled={!contenido.trim() || isSubmitting}
        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {isSubmitting ? '...' : 'Enviar'}
      </button>
    </form>
  );
}

export default MensajeComposer;
