import { defineConfig } from "vite";

// In dev, /api and /logos go to port-forwarded services:
//   kubectl port-forward svc/app-backend-svc 8103   and   kubectl port-forward svc/cdn-svc 18080:80
export default defineConfig({
  server: {
    proxy: {
      "/api": { target: "http://localhost:8103", rewrite: (p) => p.replace(/^\/api/, "") },
      // The CDN picks its logos server block by Host (server_name cdn-svc), as in-cluster.
      "/logos": { target: "http://localhost:18080", headers: { host: "cdn-svc" } },
    },
  },
});
