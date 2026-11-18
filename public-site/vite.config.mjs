import {defineConfig} from 'vite';
import {fileURLToPath} from 'node:url';
export default defineConfig({root:fileURLToPath(new URL('.',import.meta.url)),base:'/profile-assets/20261117-r1/',build:{outDir:'build',emptyOutDir:true,assetsInlineLimit:0,chunkSizeWarningLimit:600}});
