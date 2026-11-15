import { defineConfig } from "vite";

// In dev, /api and /logos go to port-forwarded services:
//   kubectl port-forward svc/app-backend-svc 8103   and   kubectl port-forward svc/cdn-svc 18080:80
// or, read-only against production: OPTIBET_LIVE=https://optibet.delavande.fr npm run dev
const live = process.env.OPTIBET_LIVE;

export default defineConfig({
  // The only chunk above Vite's 500 kB default is three.js (hero ball), loaded lazily after first paint.
  build: { chunkSizeWarningLimit: 600 },
  server: {
    proxy: live
      ? {
          "/api": { target: live, changeOrigin: true },
          "/logos": { target: live, changeOrigin: true },
        }
      : {
          "/api": { target: "http://localhost:8103", rewrite: (p) => p.replace(/^\/api/, "") },
          // The CDN picks its logos server block by Host (server_name cdn-svc), as in-cluster.
          "/logos": { target: "http://localhost:18080", headers: { host: "cdn-svc" } },
        },
  },
});
