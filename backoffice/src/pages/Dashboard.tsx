import { useAuth } from "@/context/AuthContext";

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <div>
      <h1 className="text-2xl font-semibold text-brand-ink">
        Hola, {user?.nombre?.split(" ")[0]} 👋
      </h1>
      <p className="mt-1 text-brand-muted">
        Bienvenido al Backoffice de EffiCarBroker.
      </p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <InfoCard label="Rol" value={user?.role ?? "—"} />
        <InfoCard label="Empresa (tenant)" value={user?.tenant ?? "Plataforma"} />
        <InfoCard label="Correo" value={user?.email ?? "—"} />
      </div>

      <div className="mt-8 rounded-xl border border-brand-surface-2 bg-white p-6">
        <h2 className="font-semibold text-brand-ink">Módulo 0 — Core SaaS</h2>
        <p className="mt-2 text-sm text-brand-muted">
          Autenticación, multitenancy, RBAC, auditoría y navegación dinámica están operativos.
          El menú lateral se construye desde el backend según tu rol. Los módulos de negocio
          (Tasación, Recepción, Publicación, Visitas, Liquidaciones) llegan en las siguientes
          iteraciones.
        </p>
      </div>
    </div>
  );
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-brand-surface-2 bg-white p-5">
      <p className="text-xs uppercase tracking-wide text-brand-muted">{label}</p>
      <p className="mt-1 font-medium text-brand-ink">{value}</p>
    </div>
  );
}
