import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Relative asset URLs work at both the domain root and a GitHub Pages project path.
export default defineConfig({
  base: './',
  plugins: [react()],
  server: { port: 5173 },
});
