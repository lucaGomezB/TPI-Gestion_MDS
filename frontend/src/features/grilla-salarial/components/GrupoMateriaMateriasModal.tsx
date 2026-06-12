import { useState, useEffect } from 'react';
import Modal from '@/shared/components/Modal';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import { useMateriasByGrupo, useAssignMaterias } from '../hooks/useGrupoMateria';

interface GrupoMateriaMateriasModalProps {
  grupoId: string;
  grupoNombre: string;
  isOpen: boolean;
  onClose: () => void;
}

function GrupoMateriaMateriasModal({ grupoId, grupoNombre, isOpen, onClose }: GrupoMateriaMateriasModalProps) {
  const { data: materias, isLoading, isError, refetch } = useMateriasByGrupo(grupoId);
  const assignMutation = useAssignMaterias(grupoId);
  const [materiaIds, setMateriaIds] = useState<string[]>([]);
  const [newMateriaId, setNewMateriaId] = useState('');

  useEffect(() => {
    if (materias) {
      setMateriaIds(materias.map((m) => m.materia_id));
    }
  }, [materias]);

  const handleAddMateria = () => {
    if (newMateriaId && !materiaIds.includes(newMateriaId)) {
      setMateriaIds((prev) => [...prev, newMateriaId]);
      setNewMateriaId('');
    }
  };

  const handleRemoveMateria = (id: string) => {
    setMateriaIds((prev) => prev.filter((m) => m !== id));
  };

  const handleSave = async () => {
    await assignMutation.mutateAsync({ materia_ids: materiaIds });
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Materias - ${grupoNombre}`} size="lg">
      {isLoading ? (
        <Loading message="Cargando materias..." />
      ) : isError ? (
        <ErrorDisplay message="Error al cargar materias" onRetry={() => void refetch()} />
      ) : (
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={newMateriaId}
              onChange={(e) => setNewMateriaId(e.target.value)}
              placeholder="ID de materia..."
              className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <button
              onClick={handleAddMateria}
              disabled={!newMateriaId}
              className="px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              Agregar
            </button>
          </div>

          <div className="border rounded-md divide-y">
            {materiaIds.length === 0 ? (
              <p className="text-sm text-gray-500 p-4 text-center">No hay materias asignadas</p>
            ) : (
              materiaIds.map((mid) => (
                <div key={mid} className="flex items-center justify-between px-4 py-2">
                  <span className="text-sm text-gray-700">{mid}</span>
                  <button
                    onClick={() => handleRemoveMateria(mid)}
                    className="text-sm text-red-600 hover:text-red-800 transition-colors"
                  >
                    Quitar
                  </button>
                </div>
              ))
            )}
          </div>

          <div className="flex justify-end space-x-3 pt-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              disabled={assignMutation.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {assignMutation.isPending ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}

export default GrupoMateriaMateriasModal;
