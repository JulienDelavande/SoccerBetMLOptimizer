import { defineConfig } from "vite";

// In dev, /api is proxied to a port-forwarded backend: kubectl port-forward svc/app-backend-svc 8103
export default defineConfig({
  server: { proxy: { "/api": { target: "http://localhost:8103", rewrite: (p) => p.replace(/^\/api/, "") } } },
});
