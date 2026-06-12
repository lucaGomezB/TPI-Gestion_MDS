import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Modal from '@/shared/components/Modal';
import { useSubirFactura } from '../hooks/useFacturas';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
const ACCEPTED_FORMAT = ['application/pdf'];

const subirFacturaSchema = z.object({
  periodo: z.string().regex(/^\d{4}-\d{2}$/, 'Formato YYYY-MM requerido'),
  detalle: z.string().min(1, 'El detalle es requerido').max(500),
  archivo: z
    .instanceof(FileList)
    .refine((files) => files.length > 0, 'Seleccione un archivo PDF')
    .refine((files) => files[0]?.size <= MAX_FILE_SIZE, 'El archivo debe ser menor a 10 MB')
    .refine(
      (files) => ACCEPTED_FORMAT.includes(files[0]?.type),
      'Solo se aceptan archivos PDF'
    ),
});

type SubirFacturaFormData = z.infer<typeof subirFacturaSchema>;

interface SubirFacturaModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function SubirFacturaModal({ isOpen, onClose }: SubirFacturaModalProps) {
  const uploadMutation = useSubirFactura();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<SubirFacturaFormData>({
    resolver: zodResolver(subirFacturaSchema),
  });

  const handleFormSubmit = async (data: SubirFacturaFormData) => {
    const formData = new FormData();
    formData.append('periodo', data.periodo);
    formData.append('detalle', data.detalle);
    formData.append('archivo', data.archivo[0]);

    await uploadMutation.mutateAsync(formData);
    reset();
    onClose();
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Subir factura">
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
        <div>
          <label htmlFor="fact-periodo" className="block text-sm font-medium text-gray-700">
            Periodo
          </label>
          <input
            id="fact-periodo"
            type="month"
            {...register('periodo')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          {errors.periodo && <p className="mt-1 text-sm text-red-600">{errors.periodo.message}</p>}
        </div>

        <div>
          <label htmlFor="fact-detalle" className="block text-sm font-medium text-gray-700">
            Detalle
          </label>
          <textarea
            id="fact-detalle"
            rows={3}
            {...register('detalle')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          {errors.detalle && <p className="mt-1 text-sm text-red-600">{errors.detalle.message}</p>}
        </div>

        <div>
          <label htmlFor="fact-archivo" className="block text-sm font-medium text-gray-700">
            Archivo PDF (max 10 MB)
          </label>
          <input
            id="fact-archivo"
            type="file"
            accept=".pdf,application/pdf"
            {...register('archivo')}
            className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
          {errors.archivo && (
            <p className="mt-1 text-sm text-red-600">
              {errors.archivo.message || errors.archivo.root?.message}
            </p>
          )}
        </div>

        {uploadMutation.isError && (
          <div className="p-3 rounded-md bg-red-50 text-sm text-red-700" role="alert">
            Error al subir la factura. Intente nuevamente.
          </div>
        )}

        <div className="flex justify-end space-x-3 pt-2">
          <button
            type="button"
            onClick={handleClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={uploadMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {uploadMutation.isPending ? 'Subiendo...' : 'Subir factura'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default SubirFacturaModal;
