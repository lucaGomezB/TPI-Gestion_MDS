import { useCallback, useState } from 'react';
import * as asignacionesService from '../services/asignacionesService';
import type { ExportEquipoData } from '../types/asignaciones';

export function useExportEquipo() {
  const [isExporting, setIsExporting] = useState(false);

  const exportData = useCallback(async (params: ExportEquipoData, filename = 'equipo.csv') => {
    setIsExporting(true);
    try {
      const blob = await asignacionesService.exportEquipo(params);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } finally {
      setIsExporting(false);
    }
  }, []);

  return { exportData, isExporting };
}
