import { type ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQueries } from '@tanstack/react-query';
import api from '@/shared/services/api';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import MetricCard from '@/features/materias/components/MetricCard';
import Card from '@/shared/components/Card';
import type { Materia } from '@/features/materias/types';
import type { UsuarioResponse } from '@/features/admin-usuarios/types';

interface QuickLink {
  label: string;
  path: string;
  icon: string;
}

const QUICK_LINKS: QuickLink[] = [
  { label: 'Mis Equipos', path: '/mis-equipos', icon: 'team' },
  { label: 'Materias', path: '/materias', icon: 'book' },
  { label: 'Encuentros', path: '/encuentros', icon: 'calendar' },
  { label: 'Mensajería', path: '/mensajeria', icon: 'message' },
  { label: 'Liquidaciones', path: '/liquidaciones', icon: 'dollar' },
  { label: 'Monitor General', path: '/admin/materias/monitor-general', icon: 'chart' },
];

const iconMap: Record<string, ReactNode> = {
  team: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" /></svg>,
  book: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" /></svg>,
  calendar: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" /></svg>,
  message: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" /></svg>,
  dollar: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  chart: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" /></svg>,
};

function DashboardPage(): ReactNode {
  const navigate = useNavigate();

  const [materiasQuery, usuariosQuery] = useQueries({
    queries: [
      {
        queryKey: ['dashboard', 'materias'],
        queryFn: async (): Promise<Materia[]> => {
          const { data } = await api.get<Materia[]>('/materias');
          return data;
        },
        staleTime: 5 * 60 * 1000,
        retry: 1,
      },
      {
        queryKey: ['dashboard', 'usuarios'],
        queryFn: async (): Promise<UsuarioResponse[]> => {
          const { data } = await api.get<UsuarioResponse[]>('/admin/usuarios');
          return data;
        },
        staleTime: 5 * 60 * 1000,
        retry: 1,
      },
    ],
  });

  const totalMaterias = materiasQuery.data?.length ?? 0;
  const usuarios = usuariosQuery.data;
  const totalUsuarios = usuarios?.length ?? 0;
  const usuariosActivos = usuarios?.filter((u) => u.activo).length ?? 0;
  const hasUsuariosError = usuariosQuery.isError;

  if (materiasQuery.isLoading && usuariosQuery.isLoading) {
    return (
      <div>
        <PageHeader title="Dashboard" />
        <Loading message="Cargando dashboard..." />
      </div>
    );
  }

  if (materiasQuery.isError && usuariosQuery.isError) {
    return (
      <div>
        <PageHeader title="Dashboard" />
        <ErrorDisplay
          message="No se pudo cargar la informacion del dashboard."
          onRetry={() => navigate(0)}
        />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Dashboard" />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <MetricCard label="Materias Activas" value={totalMaterias} />
        <MetricCard
          label="Usuarios Totales"
          value={hasUsuariosError ? '—' : totalUsuarios}
        />
        <MetricCard
          label="Usuarios Activos"
          value={hasUsuariosError ? '—' : usuariosActivos}
        />
      </div>

      <Card
        header={<h2 className="font-serif text-lg text-[#0F172A]">Accesos Rapidos</h2>}
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {QUICK_LINKS.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className="flex items-center gap-3 p-3 rounded-md border border-gray-200 hover:border-[#0F172A] hover:bg-gray-50 transition-colors group"
            >
              <span className="text-[#64748B] group-hover:text-[#0F172A] transition-colors">
                {iconMap[link.icon] || null}
              </span>
              <span className="text-sm font-medium text-[#334155] group-hover:text-[#0F172A] transition-colors">
                {link.label}
              </span>
            </Link>
          ))}
        </div>
      </Card>
    </div>
  );
}

export default DashboardPage;
