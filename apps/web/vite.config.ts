/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  // Reuse the repo-root .env so there's one source of truth. Vite only ever
  // exposes VITE_-prefixed variables to client code, so secrets elsewhere
  // in that file (API keys, DATABASE_URL, ...) are never bundled.
  envDir: "../../",
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg"],
      manifest: {
        name: "VaaniTrade",
        short_name: "VaaniTrade",
        description:
          "Open-source, voice-enabled Indian paper-trading assistant. Paper trading only.",
        theme_color: "#0f172a",
        background_color: "#0f172a",
        display: "standalone",
        start_url: "/",
        icons: [
          { src: "pwa-192.svg", sizes: "192x192", type: "image/svg+xml" },
          { src: "pwa-512.svg", sizes: "512x512", type: "image/svg+xml" },
        ],
      },
      devOptions: { enabled: false },
    }),
  ],
  optimizeDeps: {
    exclude: ["@vaanitrade/shared-types", "@vaanitrade/voice"],
  },
  server: {
    port: 5173,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
    exclude: ["e2e/**", "node_modules/**"],
  },
});
