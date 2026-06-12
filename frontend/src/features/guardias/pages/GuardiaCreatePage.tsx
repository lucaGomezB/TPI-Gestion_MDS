import { type ReactNode } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import GuardiaForm from '../components/GuardiaForm';
import { useCreateGuardia } from '../hooks/useCreateGuardia';
import PageHeader from '@/shared/components/PageHeader';

function GuardiaCreatePage(): ReactNode {
  const { id: materiaId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const createGuardia = useCreateGuardia(materiaId || '');

  return (
    <div>
      <PageHeader
        title="Nueva guardia"
        breadcrumbs={[
          { label: 'Materias', href: '/materias' },
          { label: 'Guardias', href: `/materias/${materiaId}/guardias` },
          { label: 'Nueva' },
        ]}
      />
      <GuardiaForm
        onSubmit={(data) =>
          createGuardia.mutate(data, {
            onSuccess: () => navigate(`/materias/${materiaId}/guardias`),
          })
        }
        isSubmitting={createGuardia.isPending}
        carreraOptions={[]}
        cohorteOptions={[]}
        asignacionOptions={[]}
      />
    </div>
  );
}

export default GuardiaCreatePage;
