import Modal from '@/shared/components/Modal';
import { useCerrarLiquidacion } from '../hooks/useLiquidaciones';

interface CerrarLiquidacionModalProps {
  liquidacionId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

function CerrarLiquidacionModal({ liquidacionId, isOpen, onClose, onSuccess }: CerrarLiquidacionModalProps) {
  const cerrarMutation = useCerrarLiquidacion();

  const handleConfirm = async () => {
    await cerrarMutation.mutateAsync(liquidacionId);
    onSuccess();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Confirmar cierre" size="sm">
      <div className="space-y-4">
        <p className="text-sm text-gray-600">
          Esta accion cerrara la liquidacion y la convertira en un registro inmutable.
          Una vez cerrada no podra modificarse (RN-22).
        </p>
        <p className="text-sm font-medium text-gray-800">Confirma que desea cerrar esta liquidacion?</p>

        {cerrarMutation.isError && (
          <div className="p-3 rounded-md bg-red-50 text-sm text-red-700" role="alert">
            Error al cerrar la liquidacion. Intente nuevamente.
          </div>
        )}

        <div className="flex justify-end space-x-3 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleConfirm}
            disabled={cerrarMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50 transition-colors"
          >
            {cerrarMutation.isPending ? 'Cerrando...' : 'Cerrar liquidacion'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

export default CerrarLiquidacionModal;
