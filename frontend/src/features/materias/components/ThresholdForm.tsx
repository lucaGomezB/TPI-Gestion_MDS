import { useState, type ReactNode } from 'react';

interface ThresholdFormProps {
  currentValue: number;
  onSubmit: (value: number) => Promise<void>;
  disabled?: boolean;
}

function ThresholdForm({ currentValue, onSubmit, disabled }: ThresholdFormProps): ReactNode {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(currentValue);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    if (isNaN(value) || value < 0 || value > 100 || !Number.isInteger(value)) {
      setError('El valor debe ser un entero entre 0 y 100');
      return;
    }
    setError(null);
    setSaving(true);
    try {
      await onSubmit(value);
      setEditing(false);
    } catch {
      setError('Error al guardar el umbral');
    } finally {
      setSaving(false);
    }
  };

  if (!editing) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">Umbral de aprobacion</p>
            <p className="text-2xl font-bold text-gray-900">{currentValue}%</p>
          </div>
          <button
            onClick={() => {
              setValue(currentValue);
              setEditing(true);
            }}
            disabled={disabled}
            className="px-3 py-1 text-sm text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50 disabled:opacity-50"
          >
            Editar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <p className="text-sm font-medium text-gray-500 mb-2">Umbral de aprobacion</p>
      <div className="flex items-center space-x-3">
        <input
          type="number"
          min={0}
          max={100}
          value={value}
          onChange={(e) => setValue(parseInt(e.target.value, 10))}
          className="w-24 px-3 py-2 text-lg font-bold border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <span className="text-lg font-bold text-gray-900">%</span>
        <button
          onClick={handleSubmit}
          disabled={saving || disabled}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Guardando...' : 'Guardar'}
        </button>
        <button
          onClick={() => setEditing(false)}
          disabled={saving}
          className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancelar
        </button>
      </div>
      {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
    </div>
  );
}

export default ThresholdForm;
