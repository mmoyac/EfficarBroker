import { useEffect, useState } from "react";
import { registerSW } from "virtual:pwa-register";

/**
 * Registra el service worker y avisa cuando hay una nueva versión de la app
 * (installable + app shell). La actualización se aplica solo si el usuario la
 * confirma: nunca se recarga en silencio para no descartar un formulario en curso.
 */
export default function PwaUpdatePrompt() {
  const [needRefresh, setNeedRefresh] = useState(false);
  const [update, setUpdate] = useState<(() => Promise<void>) | null>(null);

  useEffect(() => {
    const updateSW = registerSW({
      onNeedRefresh() {
        // `updateSW(true)` hace skipWaiting + recarga; se difiere a la acción del usuario.
        setUpdate(() => () => updateSW(true));
        setNeedRefresh(true);
      },
    });
  }, []);

  if (!needRefresh) return null;

  return (
    <div className="fixed inset-x-3 bottom-3 z-50 mx-auto flex max-w-md items-center gap-3 rounded-xl bg-brand-dark px-4 py-3 text-white shadow-lg">
      <p className="flex-1 text-sm">Hay una nueva versión disponible.</p>
      <button
        onClick={() => update?.()}
        className="rounded-lg bg-brand-accent px-3 py-1.5 text-sm font-medium text-black transition hover:bg-brand-accent-600"
      >
        Actualizar
      </button>
      <button
        onClick={() => setNeedRefresh(false)}
        className="text-sm text-brand-muted-2 hover:text-white"
        aria-label="Descartar"
      >
        Después
      </button>
    </div>
  );
}
