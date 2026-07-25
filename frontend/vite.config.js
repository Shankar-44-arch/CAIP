import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
// BUG FIX: Vite's default port is 5173 — the docker-compose port mapping
// and this dev server config must agree, or `npm run dev` binds to 5173
// while docker-compose forwards a different port, causing "connection
// refused" in the browser.
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: { '@': path.resolve(__dirname, './src') },
    },
    server: {
        host: '0.0.0.0',
        port: 5173,
        strictPort: true,
    },
    preview: {
        host: '0.0.0.0',
        port: 5173,
        strictPort: true,
    },
});
