import { useMemo, useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import EncuentroForm from '../components/EncuentroForm';
import { useCreateSlot } from '../hooks/useCreateSlot';
import { useCreateUnico } from '../hooks/useCreateUnico';
import { useMaterias } from '@/features/materias/services/useMaterias';
import PageHeader from '@/shared/components/PageHeader';
import type { CreateSlotPayload, CreateUnicoPayload } from '../types/encuentroTypes';

type Modo = 'recurrente' | 'unico';

function EncuentroCreatePage(): ReactNode {
  const navigate = useNavigate();
  const [modo, setModo] = useState<Modo>('recurrente');
  const createSlot = useCreateSlot();
  const createUnico = useCreateUnico();
  const { data: materias, isLoading: materiasLoading } = useMaterias();

  const isSubmitting = createSlot.isPending || createUnico.isPending;

  const materiasOptions = useMemo(
    () => (materias ?? []).map((m) => ({ value: m.id, label: m.nombre })),
    [materias],
  );

  const handleSubmit = (data: CreateSlotPayload | CreateUnicoPayload) => {
    if (modo === 'recurrente') {
      createSlot.mutate(data as CreateSlotPayload, {
        onSuccess: () => navigate('/encuentros'),
      });
    } else {
      createUnico.mutate(data as CreateUnicoPayload, {
        onSuccess: () => navigate('/encuentros'),
      });
    }
  };

  return (
    <div>
      <PageHeader
        title="Nuevo encuentro"
        breadcrumbs={[
          { label: 'Encuentros', href: '/encuentros' },
          { label: 'Nuevo' },
        ]}
      />
      <EncuentroForm
        modo={modo}
        onModoChange={setModo}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting || materiasLoading}
        materiasOptions={materiasOptions}
      />
    </div>
  );
}

export default EncuentroCreatePage;
