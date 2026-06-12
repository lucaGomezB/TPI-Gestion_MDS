import { useState, type ReactNode } from 'react';
import { useGenerateEmbed } from '../hooks/useGenerateEmbed';
import SnippetDisplay from '../components/SnippetDisplay';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';

function EncuentroEmbedPage(): ReactNode {
  const [materiaId, setMateriaId] = useState('');
  const [formato, setFormato] = useState<'html' | 'markdown'>('html');
  const generateEmbed = useGenerateEmbed();

  const snippet = generateEmbed.data?.snippet;

  const handleGenerate = () => {
    if (!materiaId) return;
    generateEmbed.mutate({ materiaId, formato });
  };

  return (
    <div>
      <PageHeader
        title="Generar snippet embed para Moodle"
        breadcrumbs={[
          { label: 'Encuentros', href: '/encuentros' },
          { label: 'Embed' },
        ]}
      />

      <div className="space-y-6 max-w-lg">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Materia</label>
          <select
            value={materiaId}
            onChange={(e) => setMateriaId(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">Seleccione una materia</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Formato</label>
          <div className="flex space-x-2">
            <button
              type="button"
              onClick={() => setFormato('html')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                formato === 'html' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              HTML
            </button>
            <button
              type="button"
              onClick={() => setFormato('markdown')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                formato === 'markdown' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Markdown
            </button>
          </div>
        </div>

        <button
          type="button"
          onClick={handleGenerate}
          disabled={!materiaId || generateEmbed.isPending}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {generateEmbed.isPending ? 'Generando...' : 'Generar snippet'}
        </button>

        {generateEmbed.isError && (
          <ErrorDisplay message={(generateEmbed.error as Error)?.message} onRetry={handleGenerate} />
        )}

        {generateEmbed.isSuccess && !snippet && (
          <EmptyState title="No hay encuentros programados" description="La materia seleccionada no tiene encuentros con estado Programado." />
        )}

        {snippet && <SnippetDisplay snippet={snippet} />}
      </div>
    </div>
  );
}

export default EncuentroEmbedPage;
