import { type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import ConvocatoriaForm from '../components/ConvocatoriaForm';
import { useCreateConvocatoria } from '../hooks/useCreateConvocatoria';
import PageHeader from '@/shared/components/PageHeader';

function ColoquioCreatePage(): ReactNode {
  const navigate = useNavigate();
  const createConvocatoria = useCreateConvocatoria();

  return (
    <div>
      <PageHeader
        title="Nueva convocatoria de coloquio"
        breadcrumbs={[
          { label: 'Coloquios', href: '/coloquios' },
          { label: 'Nuevo' },
        ]}
      />
      <ConvocatoriaForm
        onSubmit={(data) =>
          createConvocatoria.mutate(data, {
            onSuccess: () => navigate('/coloquios'),
          })
        }
        isSubmitting={createConvocatoria.isPending}
        materiasOptions={[]}
      />
    </div>
  );
}

export default ColoquioCreatePage;
