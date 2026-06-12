import { useState, type ReactNode } from 'react';
import { useParams } from 'react-router-dom';
import { useAgenda } from '../hooks/useAgenda';
import { useRegistrarResultado } from '../hooks/useRegistrarResultado';
import ResultadoModal from '../components/ResultadoModal';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';

function ColoquioResultadosPage(): ReactNode {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, isError, error, refetch } = useAgenda(id || '');
  const registrarResultado = useRegistrarResultado(id || '');

  const [modalOpen, setModalOpen] = useState(false);
  const [selectedAlumno, setSelectedAlumno] = useState<{ id: string; nombre: string } | null>(null);

  if (isLoading) return <Loading skeleton />;
  if (isError) return <ErrorDisplay message={(error as Error)?.message} onRetry={refetch} />;

  if (!data) return null;

  const allReservas = data.dias?.flatMap((d) => d.reservas) || [];

  const alumnosConResultado: string[] = [];

  return (
    <div>
      <PageHeader
        title="Resultados - {data.convocatoria.titulo}"
        breadcrumbs={[
          { label: 'Coloquios', href: '/coloquios' },
          { label: 'Resultados' },
        ]}
      />

      {allReservas.length === 0 ? (
        <EmptyState title="Sin reservas" description="No hay alumnos con reservas en esta convocatoria." />
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Alumno</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nota</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Aprobado</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {allReservas.map((reserva) => {
                const tieneResultado = alumnosConResultado.includes(reserva.alumno_id);
                return (
                  <tr key={reserva.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {reserva.alumno_apellido}, {reserva.alumno_nombre}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {tieneResultado ? (
                        <span className="font-medium text-gray-900">—</span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">—</td>
                    <td className="px-4 py-3 text-sm">
                      {!tieneResultado && (
                        <button
                          onClick={() => {
                            setSelectedAlumno({
                              id: reserva.alumno_id,
                              nombre: `${reserva.alumno_apellido}, ${reserva.alumno_nombre}`,
                            });
                            setModalOpen(true);
                          }}
                          className="text-blue-600 hover:text-blue-800 font-medium"
                        >
                          Registrar resultado
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <ResultadoModal
        isOpen={modalOpen}
        alumnoNombre={selectedAlumno?.nombre || ''}
        onClose={() => {
          setModalOpen(false);
          setSelectedAlumno(null);
        }}
        onConfirm={(resultado) => {
          if (!selectedAlumno || !id) return;
          registrarResultado.mutate(
            { alumno_id: selectedAlumno.id, ...resultado },
            {
              onSuccess: () => {
                setModalOpen(false);
                setSelectedAlumno(null);
                refetch();
              },
            },
          );
        }}
        isSubmitting={registrarResultado.isPending}
      />
    </div>
  );
}

export default ColoquioResultadosPage;
