import { defineConfig } from 'vite';
import angular from '@analogjs/vite-plugin-angular';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [
    angular({
      tsconfig: 'tsconfig.json',
      inlineStylesExtension: 'scss',
    }),
    tailwindcss(),
  ],
  build: {
    target: 'es2020',
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: './index.html',
      output: {
        manualChunks: {
          'angular-core': [
            '@angular/core',
            '@angular/common',
            '@angular/platform-browser',
          ],
          'angular-compiler': ['@angular/compiler'],
          'rxjs': ['rxjs'],
        },
      },
    },
    minify: 'esbuild',
    sourcemap: false,
    cssCodeSplit: true,
  },
  server: {
    port: 8080,
    host: '0.0.0.0',
  },
  preview: {
    port: 8080,
    host: '0.0.0.0',
  },
});
