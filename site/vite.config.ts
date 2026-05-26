import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// GitHub Pages project site: https://thomas-ishida.github.io/WC26-104-Game-Roadmap/
const base = "/WC26-104-Game-Roadmap/";

export default defineConfig({
  base,
  plugins: [react(), tailwindcss()],
  build: {
    outDir: "../docs",
    emptyOutDir: true,
  },
});
