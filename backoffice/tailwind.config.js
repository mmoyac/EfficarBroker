/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Identidad de marca replicada de vendemostuautomovil.com
        brand: {
          accent: "#FFD701", // amarillo dorado (botones/destacados)
          "accent-600": "#E6C200",
          dark: "#222732", // superficie oscura (sidebar/headers)
          "dark-900": "#0f141e", // dark profundo
          "dark-700": "#2f3b48",
          ink: "#1f2124", // texto principal
          muted: "#69727d", // texto atenuado
          "muted-2": "#99a1b2",
          surface: "#f2f5fb", // fondo claro
          "surface-2": "#e7edf3",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "Avenir", "Helvetica", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};
