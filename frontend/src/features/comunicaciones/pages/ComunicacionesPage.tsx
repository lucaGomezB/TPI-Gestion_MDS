import { useState, type ReactNode } from 'react';
import { useSearchParams } from 'react-router-dom';
import PageHeader from '@/shared/components/PageHeader';
import ComunicacionForm from '../components/ComunicacionForm';
import ComunicacionPreview from '../components/ComunicacionPreview';
import ComunicacionTrackingTable from '../components/ComunicacionTrackingTable';
import { useComunicaciones, usePreviewComunicacion, useEnviarComunicacion, useCancelarComunicacion } from '../hooks/useComunicaciones';
import type { ComunicacionFormValues } from '../components/ComunicacionForm';
import type { ComunicacionPreviewResponse } from '../types';

const MOCK_MATERIAS: Array<{ id: string; nombre: string }> = [
  { id: '1', nombre: 'Matemática' },
  { id: '2', nombre: 'Lengua' },
  { id: '3', nombre: 'Física' },
];

function ComunicacionesPage(): ReactNode {
  const [searchParams] = useSearchParams();
  const materiaIdFromUrl = searchParams.get('materia_id') || undefined;

  const [step, setStep] = useState<'form' | 'preview'>('form');
  const [formData, setFormData] = useState<ComunicacionFormValues | null>(null);
  const [preview, setPreview] = useState<ComunicacionPreviewResponse | null>(null);

  const { data: comunicaciones, isLoading, isError, refetch } = useComunicaciones(materiaIdFromUrl);
  const previewMutation = usePreviewComunicacion();
  const enviarMutation = useEnviarComunicacion();
  const cancelarMutation = useCancelarComunicacion();

  const handlePreview = async (data: ComunicacionFormValues) => {
    setFormData(data);
    try {
      const result = await previewMutation.mutateAsync({
        materiaId: data.materia_id,
        data: { asunto: data.asunto, cuerpo: data.cuerpo, materia_id: data.materia_id },
      });
      setPreview(result);
      setStep('preview');
    } catch {
      // Error handled by mutation
    }
  };

  const handleConfirmSend = async () => {
    if (!formData) return;
    try {
      await enviarMutation.mutateAsync({
        materiaId: formData.materia_id,
        data: {
          asunto: formData.asunto,
          cuerpo: formData.cuerpo,
          materia_id: formData.materia_id,
          requiere_aprobacion: formData.requiere_aprobacion,
        },
      });
      setStep('form');
      setFormData(null);
      setPreview(null);
    } catch {
      // Error handled by mutation
    }
  };

  const handleBack = () => {
    setStep('form');
    setPreview(null);
  };

  return (
    <div>
      <PageHeader
        title="Comunicaciones"
        breadcrumbs={[
          { label: 'Comunicaciones' },
        ]}
        actions={[
          { label: 'Nueva comunicación', onClick: () => setStep('form'), variant: 'primary' },
        ]}
      />

      {step === 'form' && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Nueva comunicación masiva</h2>
          <ComunicacionForm
            materias={MOCK_MATERIAS}
            onSubmit={handlePreview}
            isSubmitting={previewMutation.isPending}
          />
        </div>
      )}

      {step === 'preview' && preview && (
        <div className="mb-8">
          <ComunicacionPreview
            preview={preview}
            onConfirm={handleConfirmSend}
            onBack={handleBack}
            isSubmitting={enviarMutation.isPending}
          />
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Historial de envíos</h2>
        </div>
        <ComunicacionTrackingTable
          comunicaciones={comunicaciones}
          isLoading={isLoading}
          isError={isError}
          onRetry={() => refetch()}
          onCancelar={(id) => cancelarMutation.mutate(id)}
        />
      </div>
    </div>
  );
}

export default ComunicacionesPage;
