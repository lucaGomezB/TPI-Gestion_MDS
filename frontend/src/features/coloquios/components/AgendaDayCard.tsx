import { type ReactNode } from 'react';
import type { DiaAgenda } from '../types/coloquioTypes';

interface AgendaDayCardProps {
  dia: DiaAgenda;
}

function AgendaDayCard({ dia }: AgendaDayCardProps): ReactNode {
  const cuposLibres = dia.cupos - dia.reservados;

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">{dia.fecha}</h3>
          <p className="text-xs text-gray-500">
            {dia.reservados} / {dia.cupos} reservados ({cuposLibres} libres)
          </p>
        </div>
        <div className="flex space-x-1">
          <div
            className={`w-2 h-2 rounded-full ${
              cuposLibres === 0 ? 'bg-red-500' : cuposLibres <= Math.ceil(dia.cupos * 0.2) ? 'bg-yellow-500' : 'bg-green-500'
            }`}
          />
        </div>
      </div>

      {dia.reservas.length === 0 ? (
        <p className="text-sm text-gray-400 italic">Sin reservas para esta fecha</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-1 text-xs font-medium text-gray-500">Alumno</th>
                <th className="text-left py-1 text-xs font-medium text-gray-500">Confirmada</th>
              </tr>
            </thead>
            <tbody>
              {dia.reservas.map((reserva) => (
                <tr key={reserva.id} className="border-b border-gray-50">
                  <td className="py-1 text-gray-700">
                    {reserva.alumno_apellido}, {reserva.alumno_nombre}
                  </td>
                  <td className="py-1">
                    <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                      reserva.confirmada
                        ? 'bg-green-100 text-green-700'
                        : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {reserva.confirmada ? 'Sí' : 'No'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default AgendaDayCard;
