import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  server: {
    port: 5175, // explicit — avoids surprise port changes
    proxy: {
      // Any request to /api from the frontend gets forwarded to FastAPI
      "/api": {
        target: "http://localhost:8002",
        changeOrigin: true,
        // No rewrite needed — /api/v1/generate-pptx stays as-is
      },
    },
  },
});
