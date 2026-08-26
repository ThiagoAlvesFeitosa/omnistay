import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const api = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  base: "/demo/",
  server: {
    port: 5173,
    proxy: {
      "/sessoes": api,
      "/simulador": api,
      "/health": api,
      "/reservas": api,
      "/fila-do-dia": api,
    },
  },
});
