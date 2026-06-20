import { useState, type FormEvent } from 'react';
import Button from '../../../shared/components/Button';
import type { ComentarioResponse } from '../types';
import { tareasService } from '../services/tareasService';

interface ComentarioThreadProps {
  tareaId: string;
  comentarios: ComentarioResponse[];
  onComentarioAdded: (comentario: ComentarioResponse) => void;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function ComentarioThread({
  tareaId,
  comentarios,
  onComentarioAdded,
}: ComentarioThreadProps) {
  const [texto, setTexto] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = texto.trim();
    if (!trimmed) return;

    setIsSubmitting(true);
    setError(null);
    try {
      const nuevo = await tareasService.addComentario(tareaId, {
        texto: trimmed,
      });
      onComentarioAdded(nuevo);
      setTexto('');
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Error al agregar comentario',
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      {comentarios.length === 0 && (
        <p className="text-sm text-gray-500 text-center py-4">
          Sin comentarios. Se el primero en comentar.
        </p>
      )}

      {comentarios.length > 0 && (
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {comentarios.map((c) => (
            <div
              key={c.id}
              className="bg-gray-50 border border-gray-200 rounded-md p-3"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-gray-900">
                  {c.autor_id}
                </span>
                <span className="text-xs text-gray-500">
                  {formatDate(c.created_at)}
                </span>
              </div>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {c.texto}
              </p>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-2 border-t pt-3">
        <label
          htmlFor="ct-texto"
          className="block text-sm font-medium text-gray-700"
        >
          Nuevo comentario
        </label>
        <textarea
          id="ct-texto"
          rows={3}
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Escriba un comentario..."
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        {error && (
          <p className="text-xs text-red-600" role="alert">
            {error}
          </p>
        )}
        <div className="flex justify-end">
          <Button
            type="submit"
            size="sm"
            isLoading={isSubmitting}
            disabled={!texto.trim()}
          >
            Comentar
          </Button>
        </div>
      </form>
    </div>
  );
}

export default ComentarioThread;
