import { useState, useCallback, useEffect, useRef, type ReactNode } from 'react';
import { useSearchParams } from 'react-router-dom';

export interface FilterField {
  key: string;
  label: string;
  type: 'text' | 'select' | 'date' | 'number';
  options?: { value: string; label: string }[];
  placeholder?: string;
}

interface FilterBarProps {
  fields: FilterField[];
  debounceMs?: number;
}

function FilterBar({ fields, debounceMs = 0 }: FilterBarProps): ReactNode {
  const [searchParams, setSearchParams] = useSearchParams();
  const [debouncedValues, setDebouncedValues] = useState<Record<string, string>>({});
  const timersRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  // Sync initial values from URL
  useEffect(() => {
    const initial: Record<string, string> = {};
    fields.forEach((f) => {
      const val = searchParams.get(f.key);
      if (val) initial[f.key] = val;
    });
    setDebouncedValues(initial);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const updateFilter = useCallback(
    (key: string, value: string, immediate = false) => {
      if (immediate) {
        setSearchParams((prev) => {
          const next = new URLSearchParams(prev);
          if (value) {
            next.set(key, value);
          } else {
            next.delete(key);
          }
          return next;
        });
      }
    },
    [setSearchParams],
  );

  const handleImmediateChange = (key: string, value: string) => {
    updateFilter(key, value, true);
  };

  const handleDebouncedChange = (key: string, value: string) => {
    setDebouncedValues((prev) => ({ ...prev, [key]: value }));

    if (timersRef.current[key]) {
      clearTimeout(timersRef.current[key]);
    }

    timersRef.current[key] = setTimeout(() => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        if (value) {
          next.set(key, value);
        } else {
          next.delete(key);
        }
        return next;
      });
    }, debounceMs);
  };

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      Object.values(timersRef.current).forEach(clearTimeout);
    };
  }, []);

  const clearFilters = useCallback(() => {
    setSearchParams({});
    setDebouncedValues({});
  }, [setSearchParams]);

  const hasAnyFilter = fields.some((f) => searchParams.has(f.key));

  const getValue = (field: FilterField): string => {
    if (field.type === 'text' && debounceMs > 0) {
      return debouncedValues[field.key] ?? searchParams.get(field.key) ?? '';
    }
    return searchParams.get(field.key) || '';
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
      <div className="flex flex-wrap gap-3 items-end">
        {fields.map((field) => (
          <div key={field.key} className="flex flex-col">
            <label htmlFor={`filter-${field.key}`} className="text-xs font-medium text-gray-500 mb-1">
              {field.label}
            </label>
            {field.type === 'select' ? (
              <select
                id={`filter-${field.key}`}
                value={getValue(field)}
                onChange={(e) => handleImmediateChange(field.key, e.target.value)}
                className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todos</option>
                {(field.options || []).map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            ) : field.type === 'date' ? (
              <input
                id={`filter-${field.key}`}
                type="date"
                value={getValue(field)}
                onChange={(e) => handleImmediateChange(field.key, e.target.value)}
                className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            ) : field.type === 'number' ? (
              <input
                id={`filter-${field.key}`}
                type="number"
                min="0"
                value={getValue(field)}
                onChange={(e) => {
                  if (debounceMs > 0) {
                    handleDebouncedChange(field.key, e.target.value);
                  } else {
                    handleImmediateChange(field.key, e.target.value);
                  }
                }}
                placeholder={field.placeholder || field.label}
                className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            ) : (
              <input
                id={`filter-${field.key}`}
                type="text"
                value={getValue(field)}
                onChange={(e) => {
                  if (debounceMs > 0) {
                    handleDebouncedChange(field.key, e.target.value);
                  } else {
                    handleImmediateChange(field.key, e.target.value);
                  }
                }}
                placeholder={field.placeholder || field.label}
                className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            )}
          </div>
        ))}
        {hasAnyFilter && (
          <button
            onClick={clearFilters}
            className="px-3 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Limpiar filtros
          </button>
        )}
      </div>
    </div>
  );
}

export default FilterBar;
