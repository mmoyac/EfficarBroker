import { useLocation } from "react-router-dom";

export default function Placeholder() {
  const { pathname } = useLocation();
  return (
    <div className="flex h-full flex-col items-center justify-center text-center">
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-accent font-bold text-black">
        🚧
      </div>
      <h1 className="text-xl font-semibold text-brand-ink">Sección en construcción</h1>
      <p className="mt-1 text-sm text-brand-muted">
        La ruta <code className="rounded bg-brand-surface-2 px-1.5 py-0.5">{pathname}</code> se
        implementará en un módulo posterior.
      </p>
    </div>
  );
}
