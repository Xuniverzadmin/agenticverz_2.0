/**
 * AI Console - Browser Entry Point
 *
 * Role: Runtime bootstrap ONLY
 *
 * This file is the entry point for standalone deployment of AI Console
 * at console.agenticverz.com. It handles:
 * - DOM mounting
 * - BrowserRouter setup
 * - Any environment-specific configuration
 *
 * This file should NOT contain:
 * - Product routing logic
 * - Business logic
 * - Feature imports
 *
 * The product logic lives in AIConsoleApp.tsx
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { AIConsoleApp } from './app/AIConsoleApp';
import '../../index.css';

/**
 * Standalone mount for console.agenticverz.com
 *
 * When AI Console runs as a standalone product (not embedded in the
 * larger console shell), this entry provides:
 * - Its own BrowserRouter (no /console basename needed)
 * - Direct DOM mounting
 *
 * For embedded use (current state via routes/index.tsx),
 * AIConsoleApp is lazy-loaded and receives router context from parent.
 */
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AIConsoleApp />
    </BrowserRouter>
  </React.StrictMode>
);
