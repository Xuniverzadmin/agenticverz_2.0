import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE_PATH || '/',
  resolve: {
    alias: {
      // Source directory aliases
      '@': path.resolve(__dirname, './src'),
      '@ai-console': path.resolve(__dirname, './src/products/ai-console'),
      '@fops': path.resolve(__dirname, '../fops/src'),
      '@onboarding': path.resolve(__dirname, '../onboarding/src'),
      // Force external directories to use app-shell's node_modules
      'react': path.resolve(__dirname, './node_modules/react'),
      'react-dom': path.resolve(__dirname, './node_modules/react-dom'),
      'react-router-dom': path.resolve(__dirname, './node_modules/react-router-dom'),
      'axios': path.resolve(__dirname, './node_modules/axios'),
      'lucide-react': path.resolve(__dirname, './node_modules/lucide-react'),
      'clsx': path.resolve(__dirname, './node_modules/clsx'),
      '@tanstack/react-query': path.resolve(__dirname, './node_modules/@tanstack/react-query'),
      '@radix-ui/react-dialog': path.resolve(__dirname, './node_modules/@radix-ui/react-dialog'),
      '@radix-ui/react-dropdown-menu': path.resolve(__dirname, './node_modules/@radix-ui/react-dropdown-menu'),
      '@radix-ui/react-tabs': path.resolve(__dirname, './node_modules/@radix-ui/react-tabs'),
      '@radix-ui/react-tooltip': path.resolve(__dirname, './node_modules/@radix-ui/react-tooltip'),
      '@radix-ui/react-visually-hidden': path.resolve(__dirname, './node_modules/@radix-ui/react-visually-hidden'),
      'dayjs': path.resolve(__dirname, './node_modules/dayjs'),
      'recharts': path.resolve(__dirname, './node_modules/recharts'),
      'zustand': path.resolve(__dirname, './node_modules/zustand'),
    },
    dedupe: ['react', 'react-dom', 'react-router-dom', 'axios', 'lucide-react', 'clsx', '@tanstack/react-query'],
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'axios', 'lucide-react', 'clsx', '@tanstack/react-query'],
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    // Ensure rollup can resolve dependencies for all source directories
    commonjsOptions: {
      include: [/node_modules/],
    },
  },
});
