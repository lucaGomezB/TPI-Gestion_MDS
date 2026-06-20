import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './features/auth/context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import MainLayout from './components/MainLayout';
import Loading from './shared/components/Loading';
import RedirectPage from './shared/components/RedirectPage';

const LoginPage = lazy(() => import('./features/auth/pages/LoginPage'));
const TwoFactorPage = lazy(() => import('./features/auth/pages/TwoFactorPage'));
const ForgotPasswordPage = lazy(() => import('./features/auth/pages/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('./features/auth/pages/ResetPasswordPage'));
const ProfilePage = lazy(() => import('./features/auth/pages/ProfilePage'));

// Liquidaciones feature pages
const LiquidacionesPage = lazy(() => import('./features/liquidaciones/pages/LiquidacionesPage'));
const LiquidacionDetailPage = lazy(() => import('./features/liquidaciones/pages/LiquidacionDetailPage'));
const HistorialPage = lazy(() => import('./features/liquidaciones/pages/HistorialPage'));

// Grilla Salarial
const GrillaSalarialPage = lazy(() => import('./features/grilla-salarial/pages/GrillaSalarialPage'));

// Facturacion
const FacturasAdminPage = lazy(() => import('./features/facturacion/pages/FacturasAdminPage'));
const MisFacturasPage = lazy(() => import('./features/facturacion/pages/MisFacturasPage'));
const AuditLogPage = lazy(() => import('./features/auditoria/pages/AuditLogPage'));
const AuditDashboardPage = lazy(() => import('./features/auditoria/pages/AuditDashboardPage'));

const ComunicacionesPage = lazy(() => import('./features/comunicaciones/pages/ComunicacionesPage'));
const AprobacionPage = lazy(() => import('./features/comunicaciones/pages/AprobacionPage'));
const MensajesPage = lazy(() => import('./features/comunicaciones/pages/MensajesPage'));
const MensajeDetailPage = lazy(() => import('./features/comunicaciones/pages/MensajeDetailPage'));
const AvisosPage = lazy(() => import('./features/comunicaciones/pages/AvisosPage'));
const AvisoFormPage = lazy(() => import('./features/comunicaciones/pages/AvisoFormPage'));

// Encuentros
const EncuentrosLayout = lazy(() => import('./features/encuentros/pages/EncuentrosLayout'));
const EncuentrosListPage = lazy(() => import('./features/encuentros/pages/EncuentrosListPage'));
const EncuentroCreatePage = lazy(() => import('./features/encuentros/pages/EncuentroCreatePage'));
const EncuentroEditPage = lazy(() => import('./features/encuentros/pages/EncuentroEditPage'));
const EncuentroEmbedPage = lazy(() => import('./features/encuentros/pages/EncuentroEmbedPage'));
const AdminEncuentrosPage = lazy(() => import('./features/encuentros/pages/AdminEncuentrosPage'));

// Guardias
const GuardiasListPage = lazy(() => import('./features/guardias/pages/GuardiasListPage'));
const GuardiaCreatePage = lazy(() => import('./features/guardias/pages/GuardiaCreatePage'));

// Coloquios
const ColoquiosLayout = lazy(() => import('./features/coloquios/pages/ColoquiosLayout'));
const ColoquiosListPage = lazy(() => import('./features/coloquios/pages/ColoquiosListPage'));
const ColoquioCreatePage = lazy(() => import('./features/coloquios/pages/ColoquioCreatePage'));
const ColoquioAgendaPage = lazy(() => import('./features/coloquios/pages/ColoquioAgendaPage'));
const ColoquioResultadosPage = lazy(() => import('./features/coloquios/pages/ColoquioResultadosPage'));
const AdminColoquiosPage = lazy(() => import('./features/coloquios/pages/AdminColoquiosPage'));

// Materias pages
const MiSemanaPage = lazy(() => import('./features/materias/pages/MiSemanaPage'));
const MateriaDetailPage = lazy(() => import('./features/materias/pages/MateriaDetailPage'));
const AtrasadosPage = lazy(() => import('./features/materias/pages/AtrasadosPage'));
const RankingPage = lazy(() => import('./features/materias/pages/RankingPage'));
const ReportesPage = lazy(() => import('./features/materias/pages/ReportesPage'));
const NotasFinalesPage = lazy(() => import('./features/materias/pages/NotasFinalesPage'));
const ExportAtrasadosPage = lazy(() => import('./features/materias/pages/ExportAtrasadosPage'));
const SeguimientoPage = lazy(() => import('./features/materias/pages/SeguimientoPage'));
const MonitorGeneralPage = lazy(() => import('./features/materias/pages/MonitorGeneralPage'));

// Equipos / Estructura pages
const CarrerasPage = lazy(() => import('./features/estructura-academica/pages/CarrerasPage'));
const CohortesPage = lazy(() => import('./features/estructura-academica/pages/CohortesPage'));
const MateriasAdminPage = lazy(() => import('./features/estructura-academica/pages/MateriasPage'));
const DocentesPage = lazy(() => import('./features/equipos/pages/DocentesPage'));
const AsignacionesPage = lazy(() => import('./features/equipos/pages/AsignacionesPage'));
const AsignacionMasivaPage = lazy(() => import('./features/equipos/pages/AsignacionMasivaPage'));
const CloneEquipoPage = lazy(() => import('./features/equipos/pages/CloneEquipoPage'));
const VigenciaPage = lazy(() => import('./features/equipos/pages/VigenciaPage'));
const ExportEquipoPage = lazy(() => import('./features/equipos/pages/ExportEquipoPage'));
const MisEquiposPage = lazy(() => import('./features/equipos/pages/MisEquiposPage'));

// Calendario Evaluaciones
const CalendarioEvaluacionesPage = lazy(() => import('./features/calendario-evaluaciones/pages/CalendarioEvaluacionesPage'));
const AdminUsuariosPage = lazy(() => import('./features/admin-usuarios/pages/AdminUsuariosPage'));
const AdminRolesPage = lazy(() => import('./features/admin-roles/pages/AdminRolesPage'));
const TareasPage = lazy(() => import('./features/tareas-internas/pages/TareasPage'));

// Dashboard
const DashboardPage = lazy(() => import('./features/dashboard/pages/DashboardPage'));

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<Loading fullPage />}>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/two-factor" element={<TwoFactorPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />

            {/* Protected routes with MainLayout */}
            <Route
              element={
                <ProtectedRoute>
                  <MainLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={
                <RedirectPage
                  title="Activia Trace"
                  description="Seleccione un modulo del menu lateral para comenzar."
                  links={[]}
                />
              } />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/materias" element={<MiSemanaPage />} />
              <Route path="/materias/:id" element={<MateriaDetailPage />} />
              <Route path="/materias/:id/atrasados" element={<AtrasadosPage />} />
              <Route path="/materias/:id/ranking" element={<RankingPage />} />
              <Route path="/materias/:id/reportes" element={<ReportesPage />} />
              <Route path="/materias/:id/notas-finales" element={<NotasFinalesPage />} />
              <Route path="/materias/:id/export-atrasados" element={<ExportAtrasadosPage />} />
              <Route path="/materias/:id/seguimiento" element={<SeguimientoPage />} />
              <Route path="/alumnos" element={
                <RedirectPage
                  title="Alumnos"
                  description="La gestion de alumnos esta disponible desde cada materia y desde Mis Equipos."
                  links={[
                    { label: 'Ir a Materias', path: '/materias' },
                    { label: 'Ir a Mis Equipos', path: '/mis-equipos' },
                  ]}
                />
              } />
              <Route path="/comisiones" element={
                <RedirectPage
                  title="Comisiones"
                  description="Las comisiones se gestionan dentro de cada materia y asignacion docente."
                  links={[
                    { label: 'Ir a Materias', path: '/materias' },
                    { label: 'Ir a Asignaciones', path: '/admin/equipos/asignaciones' },
                  ]}
                />
              } />
              <Route path="/calificaciones" element={
                <RedirectPage
                  title="Calificaciones"
                  description="Las calificaciones se acceden desde cada materia. Seleccione una materia para importar, ver y exportar calificaciones."
                  links={[
                    { label: 'Ir a Materias', path: '/materias' },
                  ]}
                />
              } />
              <Route path="/encuentros" element={<EncuentrosLayout />}>
                <Route index element={<EncuentrosListPage />} />
                <Route path="nuevo" element={<EncuentroCreatePage />} />
                <Route path=":id/editar" element={<EncuentroEditPage />} />
                <Route path="embed/:materiaId" element={<EncuentroEmbedPage />} />
              </Route>
              <Route path="/coloquios" element={<ColoquiosLayout />}>
                <Route index element={<ColoquiosListPage />} />
                <Route path="nuevo" element={<ColoquioCreatePage />} />
                <Route path="nuevo/:materiaId" element={<ColoquioCreatePage />} />
                <Route path=":id/agenda" element={<ColoquioAgendaPage />} />
                <Route path=":id/resultados" element={<ColoquioResultadosPage />} />
              </Route>
              <Route path="/admin/encuentros" element={<AdminEncuentrosPage />} />

              <Route path="/materias/:id/guardias" element={<GuardiasListPage />} />
              <Route path="/materias/:id/guardias/nuevo" element={<GuardiaCreatePage />} />

              <Route path="/admin/coloquios" element={<AdminColoquiosPage />} />

              <Route path="/comunicaciones" element={<ComunicacionesPage />} />
              <Route path="/comunicaciones/aprobacion" element={<AprobacionPage />} />
              <Route path="/mensajeria" element={<MensajesPage />} />
              <Route path="/mensajeria/:id" element={<MensajeDetailPage />} />
              <Route path="/avisos" element={<AvisosPage />} />
              <Route path="/admin/avisos" element={<AvisoFormPage />} />
              <Route path="/admin/avisos/:id/editar" element={<AvisoFormPage />} />
              <Route path="/usuarios" element={<AdminUsuariosPage />} />
              <Route path="/roles" element={<AdminRolesPage />} />
              <Route path="/tareas-internas" element={<TareasPage />} />
              <Route path="/liquidaciones" element={<LiquidacionesPage />} />
              <Route path="/liquidaciones/historial" element={<HistorialPage />} />
              <Route path="/liquidaciones/:id" element={<LiquidacionDetailPage />} />
              <Route path="/admin/grilla-salarial" element={<GrillaSalarialPage />} />
              <Route path="/admin/facturas" element={<FacturasAdminPage />} />
              <Route path="/mis-facturas" element={<MisFacturasPage />} />
              <Route
                path="/admin/auditoria"
                element={
                  <ProtectedRoute requiredPermissions={['ADMIN', 'COORDINADOR']}>
                    <AuditLogPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/auditoria/dashboard"
                element={
                  <ProtectedRoute requiredPermissions={['ADMIN', 'COORDINADOR']}>
                    <AuditDashboardPage />
                  </ProtectedRoute>
                }
              />
              {/* Equipos / Estructura routes */}
              <Route path="/mis-equipos" element={<MisEquiposPage />} />
              <Route path="/admin/equipos/docentes" element={<DocentesPage />} />
              <Route path="/admin/equipos/asignaciones" element={<AsignacionesPage />} />
              <Route path="/admin/equipos/asignacion-masiva" element={<AsignacionMasivaPage />} />
              <Route path="/admin/equipos/clonar" element={<CloneEquipoPage />} />
              <Route path="/admin/equipos/vigencia" element={<VigenciaPage />} />
              <Route path="/admin/equipos/exportar" element={<ExportEquipoPage />} />
              <Route path="/admin/estructura/carreras" element={<CarrerasPage />} />
              <Route path="/admin/estructura/cohortes" element={<CohortesPage />} />
              <Route path="/admin/estructura/materias" element={<MateriasAdminPage />} />
              <Route
                path="/admin/materias/monitor-general"
                element={
                  <ProtectedRoute requiredPermissions={['ADMIN', 'COORDINADOR']}>
                    <MonitorGeneralPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/calendario-evaluaciones"
                element={
                  <ProtectedRoute requiredPermissions={['ADMIN', 'COORDINADOR']}>
                    <CalendarioEvaluacionesPage />
                  </ProtectedRoute>
                }
              />
              <Route path="/perfil" element={<ProfilePage />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
