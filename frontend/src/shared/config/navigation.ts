export interface NavItem {
  label: string;
  path: string;
  icon: string;
  permissions?: string[];
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

export const navigationConfig: NavSection[] = [
  {
    title: 'Académico',
    items: [
      { label: 'Mis Equipos', path: '/mis-equipos', icon: 'team', permissions: ['PROFESOR', 'TUTOR', 'NEXO', 'COORDINADOR'] },
      { label: 'Materias', path: '/materias', icon: 'book', permissions: ['ADMIN', 'COORDINADOR', 'TUTOR', 'PROFESOR'] },
      { label: 'Alumnos', path: '/alumnos', icon: 'users', permissions: ['ADMIN', 'COORDINADOR'] },
      { label: 'Comisiones', path: '/comisiones', icon: 'layers', permissions: ['ADMIN', 'COORDINADOR'] },
      { label: 'Calificaciones', path: '/calificaciones', icon: 'clipboard', permissions: ['ADMIN', 'COORDINADOR', 'TUTOR'] },
      { label: 'Encuentros', path: '/encuentros', icon: 'calendar', permissions: ['ADMIN', 'COORDINADOR', 'TUTOR'] },
      { label: 'Coloquios', path: '/coloquios', icon: 'edit', permissions: ['ADMIN', 'COORDINADOR'] },
      { label: 'Calendario Evaluaciones', path: '/admin/calendario-evaluaciones', icon: 'calendar', permissions: ['ADMIN', 'COORDINADOR'] },
    ],
  },
  {
    title: 'Equipos',
    items: [
      { label: 'Asignaciones', path: '/admin/equipos/asignaciones', icon: 'assignment', permissions: ['ADMIN', 'COORDINADOR'] },
      { label: 'Docentes', path: '/admin/equipos/docentes', icon: 'user', permissions: ['ADMIN'] },
    ],
  },
  {
    title: 'Mis Materias',
    items: [
      { label: 'Mi Semana', path: '/materias', icon: 'book', permissions: ['PROFESOR'] },
    ],
  },
  {
    title: 'Comunicaciones',
    items: [
      { label: 'Envíos masivos', path: '/comunicaciones', icon: 'message', permissions: ['ADMIN', 'COORDINADOR', 'TUTOR'] },
      { label: 'Mensajería', path: '/mensajeria', icon: 'message', permissions: ['ADMIN', 'COORDINADOR', 'TUTOR'] },
      { label: 'Avisos', path: '/avisos', icon: 'bell', permissions: ['ADMIN', 'COORDINADOR', 'TUTOR'] },
    ],
  },
  {
    title: 'Administración',
    items: [
      { label: 'Usuarios', path: '/usuarios', icon: 'users', permissions: ['ADMIN'] },
      { label: 'Roles', path: '/roles', icon: 'shield', permissions: ['ADMIN'] },
      { label: 'Carreras', path: '/admin/estructura/carreras', icon: 'book', permissions: ['ADMIN'] },
      { label: 'Cohortes', path: '/admin/estructura/cohortes', icon: 'calendar', permissions: ['ADMIN'] },
      { label: 'Materias (Admin)', path: '/admin/estructura/materias', icon: 'book-open', permissions: ['ADMIN', 'COORDINADOR'] },
      { label: 'Monitor General', path: '/admin/materias/monitor-general', icon: 'chart', permissions: ['ADMIN', 'COORDINADOR'] },
      { label: 'Tareas Internas', path: '/tareas-internas', icon: 'clipboard', permissions: ['ADMIN', 'COORDINADOR'] },
    ],
  },
  {
    title: 'Auditoría',
    items: [
      { label: 'Log de Auditoría', path: '/admin/auditoria', icon: 'clipboard', permissions: ['ADMIN', 'COORDINADOR'] },
      { label: 'Dashboard', path: '/admin/auditoria/dashboard', icon: 'chart', permissions: ['ADMIN', 'COORDINADOR'] },
    ],
  },
  {
    title: 'Reportes',
    items: [
      { label: 'Dashboard', path: '/dashboard', icon: 'chart', permissions: ['ADMIN', 'COORDINADOR', 'TUTOR'] },
      { label: 'Liquidaciones', path: '/liquidaciones', icon: 'dollar', permissions: ['ADMIN', 'COORDINADOR'] },
      { label: 'Historial', path: '/liquidaciones/historial', icon: 'clock', permissions: ['ADMIN', 'COORDINADOR'] },
      { label: 'Grilla Salarial', path: '/admin/grilla-salarial', icon: 'currency', permissions: ['ADMIN'] },
    ],
  },
  {
    title: 'Facturacion',
    items: [
      { label: 'Facturas', path: '/admin/facturas', icon: 'document', permissions: ['ADMIN'] },
      { label: 'Mis Facturas', path: '/mis-facturas', icon: 'upload', permissions: ['ADMIN', 'COORDINADOR', 'TUTOR'] },
    ],
  },
];
