/// <reference types="vitest/config" />
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const api = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "/app/",
  server: {
    port: 5173,
    proxy: {
      "/sessoes": api,
      "/simulador": api,
      "/health": api,
      "/reservas": api,
      "/fila-do-dia": api,
      "/solicitacoes": api,
      "/catalogo": api,
      "/indicadores": api,
      "/propriedade": api,
      "/consumos": api,
      "/concorrentes": api,
      "/mercado": api,
      "/retencao": api,
      "/usuarios": api,
      "/webhook": api,
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/setupTests.ts",
  },
});
