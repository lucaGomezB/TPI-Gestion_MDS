import Modal from '@/shared/components/Modal';
import { useAbonarFactura } from '../hooks/useFacturas';

interface AbonarFacturaModalProps {
  facturaId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

function AbonarFacturaModal({ facturaId, isOpen, onClose, onSuccess }: AbonarFacturaModalProps) {
  const abonarMutation = useAbonarFactura();

  const handleConfirm = async () => {
    await abonarMutation.mutateAsync(facturaId);
    onSuccess();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Confirmar pago" size="sm">
      <div className="space-y-4">
        <p className="text-sm text-gray-600">
          Marcara esta factura como <strong>Abonada</strong>. Esta accion no puede deshacerse.
        </p>
        <p className="text-sm font-medium text-gray-800">Confirma que desea abonar esta factura?</p>

        {abonarMutation.isError && (
          <div className="p-3 rounded-md bg-red-50 text-sm text-red-700" role="alert">
            Error al registrar el pago. Intente nuevamente.
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
            disabled={abonarMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            {abonarMutation.isPending ? 'Procesando...' : 'Marcar como abonada'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

export default AbonarFacturaModal;
