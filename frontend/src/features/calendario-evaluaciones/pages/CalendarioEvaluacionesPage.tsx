import { useState, useCallback, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useEvaluaciones, useCreateEvaluacion, useUpdateEvaluacion, useDeleteEvaluacion, useGenerateEmbed } from '../hooks/useEvaluaciones';
import { getMaterias } from '@/features/estructura-academica/services/estructuraService';
import { getCohortes } from '@/features/estructura-academica/services/estructuraService';
import ViewToggle from '../components/ViewToggle';
import EvaluationTable from '../components/EvaluationTable';
import EvaluationCalendar from '../components/EvaluationCalendar';
import EvaluationForm from '../components/EvaluationForm';
import CalendarEmbed from '../components/CalendarEmbed';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import type { EvaluationDate, CreateEvaluationDateData } from '../types';

// --- Task 5.1 & 5.2: CalendarioEvaluacionesPage ---

type FormData = CreateEvaluationDateData;

function CalendarioEvaluacionesPage(): ReactNode {
  // View toggle state
  const [view, setView] = useState<'table' | 'calendar'>('table');

  // Filter state
  const [filtroMateria, setFiltroMateria] = useState<string>('');
  const [filtroCohorte, setFiltroCohorte] = useState<string>('');

  // Calendar navigation state
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date());

  // Form modal state
  const [formOpen, setFormOpen] = useState(false);
  const [editingEvaluacion, setEditingEvaluacion] = useState<EvaluationDate | undefined>(undefined);

  // Embed modal state
  const [embedOpen, setEmbedOpen] = useState(false);
  const [embedCode, setEmbedCode] = useState<string | undefined>(undefined);

  // --- Data fetching ---

  const {
    data: evaluaciones = [],
    isLoading: evaluacionesLoading,
    error: evaluacionesError,
    refetch: refetchEvaluaciones,
  } = useEvaluaciones({
    materia_id: filtroMateria || undefined,
    cohorte_id: filtroCohorte || undefined,
  });

  const {
    data: materias = [],
    isLoading: materiasLoading,
    error: materiasError,
  } = useQuery({
    queryKey: ['materias'],
    queryFn: getMaterias,
  });

  const {
    data: cohortes = [],
    isLoading: cohortesLoading,
  } = useQuery({
    queryKey: ['cohortes'],
    queryFn: () => getCohortes(),
  });

  // --- Mutations ---

  const createMutation = useCreateEvaluacion();
  const updateMutation = useUpdateEvaluacion();
  const deleteMutation = useDeleteEvaluacion();
  const embedMutation = useGenerateEmbed();

  // --- Form handlers ---

  const handleOpenCreate = useCallback(() => {
    setEditingEvaluacion(undefined);
    setFormOpen(true);
  }, []);

  const handleOpenEdit = useCallback((ev: EvaluationDate) => {
    setEditingEvaluacion(ev);
    setFormOpen(true);
  }, []);

  const handleFormClose = useCallback(() => {
    setFormOpen(false);
    setEditingEvaluacion(undefined);
  }, []);

  const handleFormSubmit = useCallback(
    (data: FormData) => {
      if (editingEvaluacion && editingEvaluacion.id) {
        updateMutation.mutate(
          { id: editingEvaluacion.id, data },
          { onSuccess: () => handleFormClose() },
        );
      } else {
        createMutation.mutate(data, { onSuccess: () => handleFormClose() });
      }
    },
    [editingEvaluacion, createMutation, updateMutation, handleFormClose],
  );

  const handleDelete = useCallback(
    (id: string) => {
      if (window.confirm('Esta seguro de eliminar esta evaluacion?')) {
        deleteMutation.mutate(id);
      }
    },
    [deleteMutation],
  );

  // --- Embed handlers ---

  const handleOpenEmbed = useCallback(() => {
    setEmbedCode(undefined);
    setEmbedOpen(true);
  }, []);

  const handleEmbedClose = useCallback(() => {
    setEmbedOpen(false);
    setEmbedCode(undefined);
  }, []);

  const handleGenerateEmbed = useCallback(
    (formato: string) => {
      const materiaId = filtroMateria;
      if (!materiaId) {
        return;
      }
      embedMutation.mutate(
        { materia_id: materiaId, formato },
        {
          onSuccess: (snippet) => {
            setEmbedCode(snippet);
          },
        },
      );
    },
    [filtroMateria, embedMutation],
  );

  // Select options
  const materiaOptions = materias.map((m) => ({
    value: m.id!,
    label: m.nombre,
  }));

  const cohorteOptions = cohortes.map((c) => ({
    value: c.id!,
    label: c.nombre,
  }));

  // Combined loading / error for initial data
  if (materiasLoading && cohortesLoading) {
    return <Loading skeleton />;
  }

  if (materiasError) {
    return <ErrorDisplay message="Error al cargar materias" onRetry={refetchEvaluaciones} />;
  }

  return (
    <div>
      <PageHeader
        title="Calendario de Evaluaciones"
        breadcrumbs={[
          { label: 'Administracion', href: '/admin' },
          { label: 'Calendario Evaluaciones' },
        ]}
        actions={[
          {
            label: 'Nueva Evaluacion',
            onClick: handleOpenCreate,
            variant: 'primary',
          },
          {
            label: 'Generar Embed',
            onClick: handleOpenEmbed,
            variant: 'secondary',
          },
        ]}
      />

      {/* Filter bar + View toggle */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        <ViewToggle view={view} onViewChange={setView} />

        <div className="flex items-center gap-3 flex-1">
          <select
            value={filtroMateria}
            onChange={(e) => {
              setFiltroMateria(e.target.value);
              setFiltroCohorte('');
            }}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm min-w-[200px]"
          >
            <option value="">Todas las materias</option>
            {materiaOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <select
            value={filtroCohorte}
            onChange={(e) => setFiltroCohorte(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm min-w-[200px]"
          >
            <option value="">Todos los cohortes</option>
            {cohorteOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Content: Table or Calendar */}
      {view === 'table' ? (
        <EvaluationTable
          evaluaciones={evaluaciones}
          isLoading={evaluacionesLoading}
          error={evaluacionesError as Error | null}
          onEdit={handleOpenEdit}
          onDelete={handleDelete}
          onRetry={() => refetchEvaluaciones()}
        />
      ) : (
        <EvaluationCalendar
          evaluaciones={evaluaciones}
          isLoading={evaluacionesLoading}
          error={evaluacionesError as Error | null}
          currentMonth={currentMonth}
          onMonthChange={setCurrentMonth}
          onRetry={() => refetchEvaluaciones()}
        />
      )}

      {/* Evaluation Form Modal */}
      <EvaluationForm
        isOpen={formOpen}
        onClose={handleFormClose}
        onSubmit={handleFormSubmit}
        initialData={editingEvaluacion}
        materias={materiaOptions}
        cohortes={cohorteOptions}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
      />

      {/* Calendar Embed Modal */}
      <CalendarEmbed
        isOpen={embedOpen}
        onClose={handleEmbedClose}
        onGenerate={handleGenerateEmbed}
        embedCode={embedCode}
        isLoading={embedMutation.isPending}
      />
    </div>
  );
}

export default CalendarioEvaluacionesPage;
