import { useAuth } from '../context/AuthContext';
import PageHeader from '@/shared/components/PageHeader';
import Card from '@/shared/components/Card';
import Badge from '@/shared/components/Badge';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';

interface FieldRowProps {
  label: string;
  value: string;
}

function FieldRow({ label, value }: FieldRowProps) {
  return (
    <div>
      <label className="block text-label-sm text-tertiary mb-1">{label}</label>
      <p className="text-body-md text-primary">{value || '\u2014'}</p>
    </div>
  );
}

function ProfilePage() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <Loading />;
  }

  if (!user) {
    return (
      <ErrorDisplay message="No se pudo cargar la informacion del perfil. Intente iniciar sesion nuevamente." />
    );
  }

  const roles = user.rol
    ? user.rol.split(',').map((r) => r.trim()).filter(Boolean)
    : [];

  return (
    <div>
      <PageHeader
        title="Perfil"
        breadcrumbs={[
          { label: 'Inicio', href: '/' },
          { label: 'Perfil' },
        ]}
      />

      <div className="max-w-2xl">
        <Card>
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <FieldRow label="Nombre" value={user.nombre} />
              <FieldRow label="Apellidos" value={user.apellidos} />
            </div>

            <FieldRow label="Correo Electronico" value={user.email} />

            <div>
              <label className="block text-label-sm text-tertiary mb-2">Roles</label>
              <div className="flex gap-2 flex-wrap">
                {roles.length > 0 ? (
                  roles.map((rol) => (
                    <Badge key={rol} variant="info">
                      {rol}
                    </Badge>
                  ))
                ) : (
                  <span className="text-body-md text-tertiary">{'\u2014'}</span>
                )}
              </div>
            </div>

            <FieldRow label="Tenant ID" value={user.tenant_id} />
          </div>
        </Card>
      </div>
    </div>
  );
}

export default ProfilePage;
