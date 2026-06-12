import { useState, useMemo, type ReactNode } from 'react';
import type { EvaluationDate } from '../types';

interface EvaluationCalendarProps {
  evaluaciones: EvaluationDate[];
  isLoading: boolean;
  error: Error | null;
  currentMonth: Date;
  onMonthChange: (date: Date) => void;
  onRetry: () => void;
}

const DAYS_OF_WEEK = ['Dom', 'Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab'];

const tipoBadgeColors: Record<string, string> = {
  Parcial: 'bg-blue-100 text-blue-800',
  TP: 'bg-green-100 text-green-800',
  Coloquio: 'bg-purple-100 text-purple-800',
};

function getMonthDays(year: number, month: number): (number | null)[] {
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const days: (number | null)[] = [];

  for (let i = 0; i < firstDay; i++) {
    days.push(null);
  }

  for (let d = 1; d <= daysInMonth; d++) {
    days.push(d);
  }

  while (days.length % 7 !== 0) {
    days.push(null);
  }

  return days;
}

function pad(n: number): string {
  return n.toString().padStart(2, '0');
}

function EvaluationCalendar({
  evaluaciones,
  isLoading,
  error,
  currentMonth,
  onMonthChange,
  onRetry,
}: EvaluationCalendarProps): ReactNode {
  const [selectedDay, setSelectedDay] = useState<number | null>(null);

  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();

  const monthName = currentMonth.toLocaleDateString('es-AR', { month: 'long', year: 'numeric' });

  const days = useMemo(() => getMonthDays(year, month), [year, month]);

  // Group evaluations by day
  const evaluationsByDay = useMemo(() => {
    const map = new Map<number, EvaluationDate[]>();
    for (const ev of evaluaciones) {
      const d = parseInt(ev.fecha.split('-')[2], 10);
      const existing = map.get(d) || [];
      existing.push(ev);
      map.set(d, existing);
    }
    return map;
  }, [evaluaciones]);

  const navigateMonth = (delta: number) => {
    const newDate = new Date(year, month + delta, 1);
    onMonthChange(newDate);
    setSelectedDay(null);
  };

  const isCurrentMonth = (d: number): boolean => {
    const today = new Date();
    return today.getFullYear() === year && today.getMonth() === month && today.getDate() === d;
  };

  // --- Task 7.1: Loading state ---
  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3 p-4">
        <div className="h-8 bg-gray-200 rounded w-1/3 mx-auto" />
        <div className="grid grid-cols-7 gap-1">
          {Array.from({ length: 35 }).map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    );
  }

  // --- Task 7.2: Error state ---
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center" role="alert">
        <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mb-4">
          <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
        </div>
        <p className="text-sm font-medium text-red-800 mb-4">{error.message || 'Error al cargar evaluaciones'}</p>
        <button
          onClick={onRetry}
          className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 transition-colors"
        >
          Reintentar
        </button>
      </div>
    );
  }

  const selectedEvaluations = selectedDay ? evaluationsByDay.get(selectedDay) || [] : [];

  return (
    <div>
      {/* Navigation */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => navigateMonth(-1)}
          className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          &larr; Anterior
        </button>
        <h3 className="text-lg font-semibold text-gray-900 capitalize">{monthName}</h3>
        <button
          onClick={() => navigateMonth(1)}
          className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          Siguiente &rarr;
        </button>
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-px bg-gray-200 rounded-lg overflow-hidden">
        {/* Day headers */}
        {DAYS_OF_WEEK.map((d) => (
          <div key={d} className="bg-gray-50 px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase">
            {d}
          </div>
        ))}

        {/* Day cells */}
        {days.map((day, idx) => {
          if (day === null) {
            return <div key={`empty-${idx}`} className="bg-white min-h-[80px]" />;
          }

          const dayEvaluations = evaluationsByDay.get(day) || [];
          const isToday = isCurrentMonth(day);
          const isSelected = selectedDay === day;

          return (
            <div
              key={day}
              onClick={() => setSelectedDay(isSelected ? null : day)}
              className={`bg-white min-h-[80px] p-1 cursor-pointer hover:bg-gray-50 transition-colors ${
                isToday ? 'ring-2 ring-blue-400 ring-inset' : ''
              } ${isSelected ? 'bg-blue-50' : ''}`}
            >
              <span className={`text-xs font-medium ${isToday ? 'text-blue-600' : 'text-gray-700'}`}>
                {day}
              </span>
              {dayEvaluations.length > 0 && (
                <div className="mt-1 space-y-0.5">
                  {dayEvaluations.slice(0, 3).map((ev) => (
                    <span
                      key={ev.id}
                      className={`block text-[10px] px-1 py-0.5 rounded truncate ${
                        tipoBadgeColors[ev.tipo] || 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {ev.tipo}
                    </span>
                  ))}
                  {dayEvaluations.length > 3 && (
                    <span className="block text-[10px] text-gray-400 px-1">
                      +{dayEvaluations.length - 3} más
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* --- Task 7.3: Empty state for selected day --- */}
      {selectedDay !== null && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
            Evaluaciones - {pad(selectedDay)}/{pad(month + 1)}/{year}
          </h4>
          {selectedEvaluations.length === 0 ? (
            <p className="text-sm text-gray-500">No hay evaluaciones en esta fecha.</p>
          ) : (
            <ul className="space-y-2">
              {selectedEvaluations.map((ev) => (
                <li key={ev.id} className="text-sm text-gray-700 flex items-center gap-2">
                  <span className={`inline-block w-2 h-2 rounded-full ${
                    ev.tipo === 'Parcial' ? 'bg-blue-500' : ev.tipo === 'TP' ? 'bg-green-500' : 'bg-purple-500'
                  }`} />
                  <span className="font-medium">{ev.titulo}</span>
                  <span className="text-gray-400">- {ev.tipo} #{ev.numero_instancia}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Empty month state */}
      {evaluaciones.length === 0 && selectedDay === null && (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <p className="text-sm text-gray-500">No hay evaluaciones en este mes.</p>
        </div>
      )}
    </div>
  );
}

export default EvaluationCalendar;
