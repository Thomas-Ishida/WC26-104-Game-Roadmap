import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Set base to '/your-repo-name/' for GitHub project pages (see README)
const base = "/";

export default defineConfig({
  base,
  plugins: [react(), tailwindcss()],
  build: {
    outDir: "../docs",
    emptyOutDir: true,
  },
});
