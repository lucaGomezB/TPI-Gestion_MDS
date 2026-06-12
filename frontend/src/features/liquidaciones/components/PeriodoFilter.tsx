interface PeriodoFilterProps {
  value: string;
  onChange: (periodo: string) => void;
}

function PeriodoFilter({ value, onChange }: PeriodoFilterProps) {
  return (
    <div className="flex items-center space-x-2">
      <label htmlFor="periodo" className="text-sm font-medium text-gray-700">
        Periodo:
      </label>
      <input
        id="periodo"
        type="month"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
    </div>
  );
}

export default PeriodoFilter;
