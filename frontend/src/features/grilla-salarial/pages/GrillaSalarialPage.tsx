import { useState } from 'react';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import Modal from '@/shared/components/Modal';
import { useSalarioBaseList, useSalarioBaseCreate, useSalarioBaseUpdate } from '../hooks/useSalarioBase';
import { useSalarioPlusList, useSalarioPlusCreate, useSalarioPlusUpdate } from '../hooks/useSalarioPlus';
import { useGrupoMateriaList, useGrupoMateriaCreate, useGrupoMateriaUpdate } from '../hooks/useGrupoMateria';
import SalarioBaseForm from '../components/SalarioBaseForm';
import SalarioPlusForm from '../components/SalarioPlusForm';
import GrupoMateriaForm from '../components/GrupoMateriaForm';
import GrupoMateriaMateriasModal from '../components/GrupoMateriaMateriasModal';
import type { SalarioBase, SalarioPlus, GrupoMateria, SalarioBaseCreate, SalarioBaseUpdate, SalarioPlusCreate, SalarioPlusUpdate, GrupoMateriaCreate, GrupoMateriaUpdate } from '../types';

type Tab = 'base' | 'plus' | 'grupos';

function GrillaSalarialPage() {
  const [activeTab, setActiveTab] = useState<Tab>('base');
  const [modalOpen, setModalOpen] = useState(false);
  const [editItem, setEditItem] = useState<SalarioBase | SalarioPlus | GrupoMateria | null>(null);
  const [materiasModal, setMateriasModal] = useState<{ id: string; nombre: string } | null>(null);

  const baseQuery = useSalarioBaseList();
  const plusQuery = useSalarioPlusList();
  const gruposQuery = useGrupoMateriaList();
  const baseCreate = useSalarioBaseCreate();
  const baseUpdate = useSalarioBaseUpdate(editItem?.id ?? '');
  const plusCreate = useSalarioPlusCreate();
  const plusUpdate = useSalarioPlusUpdate(editItem?.id ?? '');
  const grupoCreate = useGrupoMateriaCreate();
  const grupoUpdate = useGrupoMateriaUpdate(editItem?.id ?? '');

  const handleOpenCreate = () => {
    setEditItem(null);
    setModalOpen(true);
  };

  const handleOpenEdit = (item: SalarioBase | SalarioPlus | GrupoMateria) => {
    setEditItem(item);
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setEditItem(null);
  };

  const handleBaseSubmit = async (data: SalarioBaseCreate | SalarioBaseUpdate) => {
    if (editItem) {
      await baseUpdate.mutateAsync(data as SalarioBaseUpdate);
    } else {
      await baseCreate.mutateAsync(data as SalarioBaseCreate);
    }
    handleCloseModal();
  };

  const handlePlusSubmit = async (data: SalarioPlusCreate | SalarioPlusUpdate) => {
    if (editItem) {
      await plusUpdate.mutateAsync(data as SalarioPlusUpdate);
    } else {
      await plusCreate.mutateAsync(data as SalarioPlusCreate);
    }
    handleCloseModal();
  };

  const handleGrupoSubmit = async (data: GrupoMateriaCreate | GrupoMateriaUpdate) => {
    if (editItem) {
      await grupoUpdate.mutateAsync(data as GrupoMateriaUpdate);
    } else {
      await grupoCreate.mutateAsync(data as GrupoMateriaCreate);
    }
    handleCloseModal();
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: 'base', label: 'Salario Base' },
    { key: 'plus', label: 'Salario Plus' },
    { key: 'grupos', label: 'Grupos' },
  ];

  const getFormContent = () => {
    switch (activeTab) {
      case 'base':
        return (
          <SalarioBaseForm
            initialData={editItem as SalarioBase | undefined}
            onSubmit={handleBaseSubmit}
            onCancel={handleCloseModal}
            isSubmitting={baseCreate.isPending || baseUpdate.isPending}
          />
        );
      case 'plus':
        return (
          <SalarioPlusForm
            initialData={editItem as SalarioPlus | undefined}
            onSubmit={handlePlusSubmit}
            onCancel={handleCloseModal}
            isSubmitting={plusCreate.isPending || plusUpdate.isPending}
          />
        );
      case 'grupos':
        return (
          <GrupoMateriaForm
            initialData={editItem as GrupoMateria | undefined}
            onSubmit={handleGrupoSubmit}
            onCancel={handleCloseModal}
            isSubmitting={grupoCreate.isPending || grupoUpdate.isPending}
          />
        );
    }
  };

  const handleSubmitForm = () => getFormContent();

  return (
    <div>
      <PageHeader
        title="Grilla Salarial"
        breadcrumbs={[
          { label: 'Administracion', href: '/' },
          { label: 'Grilla Salarial' },
        ]}
        actions={[{ label: 'Nuevo', onClick: handleOpenCreate }]}
      />

      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'base' && (
        <BaseTabContent
          data={baseQuery.data}
          isLoading={baseQuery.isLoading}
          isError={baseQuery.isError}
          onRetry={() => void baseQuery.refetch()}
          onEdit={handleOpenEdit}
        />
      )}
      {activeTab === 'plus' && (
        <PlusTabContent
          data={plusQuery.data}
          isLoading={plusQuery.isLoading}
          isError={plusQuery.isError}
          onRetry={() => void plusQuery.refetch()}
          onEdit={handleOpenEdit}
        />
      )}
      {activeTab === 'grupos' && (
        <GruposTabContent
          data={gruposQuery.data}
          isLoading={gruposQuery.isLoading}
          isError={gruposQuery.isError}
          onRetry={() => void gruposQuery.refetch()}
          onEdit={handleOpenEdit}
          onManageMaterias={(g) => setMateriasModal({ id: g.id, nombre: g.grupo })}
        />
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={handleCloseModal}
        title={editItem ? 'Editar' : 'Nuevo'}
      >
        {handleSubmitForm()}
      </Modal>

      {/* Materias Assignment Modal */}
      {materiasModal && (
        <GrupoMateriaMateriasModal
          grupoId={materiasModal.id}
          grupoNombre={materiasModal.nombre}
          isOpen={!!materiasModal}
          onClose={() => setMateriasModal(null)}
        />
      )}
    </div>
  );
}

// ── Sub-components for tab content ──────────────────────────────────────

interface TabContentProps<T> {
  data: T[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
  onEdit: (item: T) => void;
}

function BaseTabContent({ data, isLoading, isError, onRetry, onEdit }: TabContentProps<SalarioBase>) {
  if (isLoading) return <Loading skeleton />;
  if (isError) return <ErrorDisplay message="Error al cargar salarios base" onRetry={onRetry} />;
  if (!data || data.length === 0) {
    return <EmptyState title="Sin salarios base" description="No hay salarios base configurados." />;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rol</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Monto</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vigencia desde</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vigencia hasta</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm font-medium text-gray-900">{item.rol}</td>
              <td className="px-4 py-3 text-sm text-gray-700">${item.monto.toFixed(2)}</td>
              <td className="px-4 py-3 text-sm text-gray-700">{item.desde}</td>
              <td className="px-4 py-3 text-sm text-gray-700">{item.hasta || '-'}</td>
              <td className="px-4 py-3 text-sm text-right">
                <button onClick={() => onEdit(item)} className="text-blue-600 hover:text-blue-800 transition-colors">
                  Editar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PlusTabContent({ data, isLoading, isError, onRetry, onEdit }: TabContentProps<SalarioPlus>) {
  if (isLoading) return <Loading skeleton />;
  if (isError) return <ErrorDisplay message="Error al cargar salarios plus" onRetry={onRetry} />;
  if (!data || data.length === 0) {
    return <EmptyState title="Sin salarios plus" description="No hay salarios plus configurados." />;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grupo</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rol</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Descripcion</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Monto</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vigencia</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm font-medium text-gray-900">{item.grupo}</td>
              <td className="px-4 py-3 text-sm text-gray-700">{item.rol}</td>
              <td className="px-4 py-3 text-sm text-gray-700">{item.descripcion}</td>
              <td className="px-4 py-3 text-sm text-gray-700">${item.monto.toFixed(2)}</td>
              <td className="px-4 py-3 text-sm text-gray-700">{item.desde} - {item.hasta || '∞'}</td>
              <td className="px-4 py-3 text-sm text-right">
                <button onClick={() => onEdit(item)} className="text-blue-600 hover:text-blue-800 transition-colors">
                  Editar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface GruposTabContentProps extends TabContentProps<GrupoMateria> {
  onManageMaterias: (grupo: GrupoMateria) => void;
}

function GruposTabContent({ data, isLoading, isError, onRetry, onEdit, onManageMaterias }: GruposTabContentProps) {
  if (isLoading) return <Loading skeleton />;
  if (isError) return <ErrorDisplay message="Error al cargar grupos" onRetry={onRetry} />;
  if (!data || data.length === 0) {
    return <EmptyState title="Sin grupos" description="No hay grupos de materia configurados." />;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grupo</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Descripcion</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm font-medium text-gray-900">{item.grupo}</td>
              <td className="px-4 py-3 text-sm text-gray-700">{item.descripcion || '-'}</td>
              <td className="px-4 py-3 text-sm text-right space-x-3">
                <button onClick={() => onEdit(item)} className="text-blue-600 hover:text-blue-800 transition-colors">
                  Editar
                </button>
                <button onClick={() => onManageMaterias(item)} className="text-green-600 hover:text-green-800 transition-colors">
                  Materias
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default GrillaSalarialPage;
