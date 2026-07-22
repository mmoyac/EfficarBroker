import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import path from "node:path";

// El manifest y los iconos NO los genera el plugin: los sirve el backend de
// forma host-aware (por dominio → tenant). Por eso `manifest: false` y el
// `<link rel="manifest">` va escrito a mano en index.html apuntando al backend.
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "prompt", // el usuario decide cuándo actualizar (no recarga silenciosa)
      injectRegister: null, // registro manual desde main.tsx
      manifest: false,
      workbox: {
        // Precache del app shell (assets con hash de Vite). El HTML no se precachea:
        // se sirve network-first para no entregar un index.html obsoleto tras deploy.
        globPatterns: ["**/*.{js,css,ico,svg,woff,woff2}"],
        navigateFallback: null,
        runtimeCaching: [
          {
            // Navegaciones (documento HTML): red primero, cae a caché sin conexión.
            urlPattern: ({ request }) => request.mode === "navigate",
            handler: "NetworkFirst",
            options: { cacheName: "html", networkTimeoutSeconds: 3 },
          },
          {
            // Datos y respuestas autenticadas: SIEMPRE a la red, nunca cacheadas.
            urlPattern: ({ url }) =>
              url.pathname.startsWith("/api/") ||
              url.pathname.startsWith("/media/") ||
              url.pathname.startsWith("/app-icons/") ||
              url.pathname === "/manifest.webmanifest",
            handler: "NetworkOnly",
          },
        ],
      },
      devOptions: { enabled: false }, // el SW se prueba en build/preview, no en `npm run dev`
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    port: 5173,
    host: true,
    // En dev el front (5173) y el backend (8000) son orígenes distintos. El
    // manifest/iconos deben resolverse en el MISMO origen que la página, así que
    // se proxean al backend (en dev el Host es localhost → identidad por defecto).
    proxy: {
      "/manifest.webmanifest": "http://localhost:8000",
      "/app-icons": "http://localhost:8000",
      "/media": "http://localhost:8000",
    },
  },
});
