# AOS Console UI Design System

**Version:** 1.0.0
**Created:** 2025-12-13
**Framework:** Tailwind CSS + CSS Custom Properties

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Color System](#color-system)
3. [Typography](#typography)
4. [Spacing Scale](#spacing-scale)
5. [Border Radius](#border-radius)
6. [Shadows](#shadows)
7. [Breakpoints](#breakpoints)
8. [Animation](#animation)
9. [Component Styles](#component-styles)
10. [Dark Mode](#dark-mode)
11. [Design Tokens](#design-tokens)
12. [Iconography](#iconography)

---

## Design Principles

### 1. Machine-Native Clarity
- Data-first design: prioritize information density
- Clear visual hierarchy for scan-ability
- Minimal decoration, maximum function

### 2. Operational Excellence
- Real-time feedback for all actions
- Status visibility at a glance
- Error states are informative, not alarming

### 3. Professional Trust
- Consistent, predictable interactions
- Enterprise-grade aesthetic
- Accessibility as a core feature

### 4. Performance Focus
- Fast perceived load times
- Skeleton states over spinners
- Progressive enhancement

---

## Color System

### Brand Colors

```css
/* Primary - Deep Blue (Trust, Technology) */
--color-primary-50: #eff6ff;
--color-primary-100: #dbeafe;
--color-primary-200: #bfdbfe;
--color-primary-300: #93c5fd;
--color-primary-400: #60a5fa;
--color-primary-500: #3b82f6;   /* Primary */
--color-primary-600: #2563eb;
--color-primary-700: #1d4ed8;
--color-primary-800: #1e40af;
--color-primary-900: #1e3a8a;
--color-primary-950: #172554;

/* Secondary - Slate (Neutral, Professional) */
--color-secondary-50: #f8fafc;
--color-secondary-100: #f1f5f9;
--color-secondary-200: #e2e8f0;
--color-secondary-300: #cbd5e1;
--color-secondary-400: #94a3b8;
--color-secondary-500: #64748b;   /* Secondary */
--color-secondary-600: #475569;
--color-secondary-700: #334155;
--color-secondary-800: #1e293b;
--color-secondary-900: #0f172a;
--color-secondary-950: #020617;

/* Accent - Violet (Innovation, AI) */
--color-accent-50: #f5f3ff;
--color-accent-100: #ede9fe;
--color-accent-200: #ddd6fe;
--color-accent-300: #c4b5fd;
--color-accent-400: #a78bfa;
--color-accent-500: #8b5cf6;   /* Accent */
--color-accent-600: #7c3aed;
--color-accent-700: #6d28d9;
--color-accent-800: #5b21b6;
--color-accent-900: #4c1d95;
--color-accent-950: #2e1065;
```

### Semantic Colors

```css
/* Success - Green */
--color-success-50: #f0fdf4;
--color-success-100: #dcfce7;
--color-success-200: #bbf7d0;
--color-success-300: #86efac;
--color-success-400: #4ade80;
--color-success-500: #22c55e;   /* Success */
--color-success-600: #16a34a;
--color-success-700: #15803d;
--color-success-800: #166534;
--color-success-900: #14532d;

/* Warning - Amber */
--color-warning-50: #fffbeb;
--color-warning-100: #fef3c7;
--color-warning-200: #fde68a;
--color-warning-300: #fcd34d;
--color-warning-400: #fbbf24;
--color-warning-500: #f59e0b;   /* Warning */
--color-warning-600: #d97706;
--color-warning-700: #b45309;
--color-warning-800: #92400e;
--color-warning-900: #78350f;

/* Error - Red */
--color-error-50: #fef2f2;
--color-error-100: #fee2e2;
--color-error-200: #fecaca;
--color-error-300: #fca5a5;
--color-error-400: #f87171;
--color-error-500: #ef4444;   /* Error */
--color-error-600: #dc2626;
--color-error-700: #b91c1c;
--color-error-800: #991b1b;
--color-error-900: #7f1d1d;

/* Info - Cyan */
--color-info-50: #ecfeff;
--color-info-100: #cffafe;
--color-info-200: #a5f3fc;
--color-info-300: #67e8f9;
--color-info-400: #22d3ee;
--color-info-500: #06b6d4;   /* Info */
--color-info-600: #0891b2;
--color-info-700: #0e7490;
--color-info-800: #155e75;
--color-info-900: #164e63;
```

### Background Colors

```css
/* Light Mode */
--bg-primary: #ffffff;
--bg-secondary: #f8fafc;
--bg-tertiary: #f1f5f9;
--bg-elevated: #ffffff;
--bg-overlay: rgba(15, 23, 42, 0.5);

/* Surface Colors */
--surface-default: #ffffff;
--surface-raised: #ffffff;
--surface-sunken: #f1f5f9;
--surface-overlay: #ffffff;
```

### Text Colors

```css
/* Light Mode */
--text-primary: #0f172a;
--text-secondary: #475569;
--text-tertiary: #64748b;
--text-disabled: #94a3b8;
--text-inverse: #ffffff;
--text-link: #2563eb;
--text-link-hover: #1d4ed8;
```

### Border Colors

```css
--border-default: #e2e8f0;
--border-hover: #cbd5e1;
--border-focus: #3b82f6;
--border-error: #ef4444;
--border-success: #22c55e;
```

---

## Typography

### Font Family

```css
/* Primary Font - Inter (UI) */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

/* Monospace - JetBrains Mono (Code) */
--font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
```

### Type Scale

```css
/* Display */
--text-display-2xl: 4.5rem;    /* 72px */
--text-display-xl: 3.75rem;    /* 60px */
--text-display-lg: 3rem;       /* 48px */
--text-display-md: 2.25rem;    /* 36px */
--text-display-sm: 1.875rem;   /* 30px */

/* Headings */
--text-heading-xl: 1.5rem;     /* 24px */
--text-heading-lg: 1.25rem;    /* 20px */
--text-heading-md: 1.125rem;   /* 18px */
--text-heading-sm: 1rem;       /* 16px */

/* Body */
--text-body-lg: 1.125rem;      /* 18px */
--text-body-md: 1rem;          /* 16px - Default */
--text-body-sm: 0.875rem;      /* 14px */
--text-body-xs: 0.75rem;       /* 12px */

/* Labels */
--text-label-lg: 0.875rem;     /* 14px */
--text-label-md: 0.75rem;      /* 12px */
--text-label-sm: 0.6875rem;    /* 11px */
```

### Line Heights

```css
--leading-none: 1;
--leading-tight: 1.25;
--leading-snug: 1.375;
--leading-normal: 1.5;
--leading-relaxed: 1.625;
--leading-loose: 2;
```

### Font Weights

```css
--font-thin: 100;
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
--font-extrabold: 800;
```

### Text Styles (Composite)

```css
/* Display Styles */
.text-display-2xl {
  font-size: var(--text-display-2xl);
  line-height: var(--leading-tight);
  font-weight: var(--font-bold);
  letter-spacing: -0.025em;
}

/* Heading Styles */
.text-heading-xl {
  font-size: var(--text-heading-xl);
  line-height: var(--leading-tight);
  font-weight: var(--font-semibold);
  letter-spacing: -0.01em;
}

.text-heading-lg {
  font-size: var(--text-heading-lg);
  line-height: var(--leading-snug);
  font-weight: var(--font-semibold);
}

/* Body Styles */
.text-body-md {
  font-size: var(--text-body-md);
  line-height: var(--leading-normal);
  font-weight: var(--font-normal);
}

/* Label Styles */
.text-label-md {
  font-size: var(--text-label-md);
  line-height: var(--leading-normal);
  font-weight: var(--font-medium);
  letter-spacing: 0.025em;
  text-transform: uppercase;
}

/* Monospace */
.text-mono {
  font-family: var(--font-mono);
  font-size: 0.9em;
}
```

---

## Spacing Scale

```css
/* Base unit: 4px */
--space-0: 0;
--space-px: 1px;
--space-0.5: 0.125rem;   /* 2px */
--space-1: 0.25rem;      /* 4px */
--space-1.5: 0.375rem;   /* 6px */
--space-2: 0.5rem;       /* 8px */
--space-2.5: 0.625rem;   /* 10px */
--space-3: 0.75rem;      /* 12px */
--space-3.5: 0.875rem;   /* 14px */
--space-4: 1rem;         /* 16px */
--space-5: 1.25rem;      /* 20px */
--space-6: 1.5rem;       /* 24px */
--space-7: 1.75rem;      /* 28px */
--space-8: 2rem;         /* 32px */
--space-9: 2.25rem;      /* 36px */
--space-10: 2.5rem;      /* 40px */
--space-11: 2.75rem;     /* 44px */
--space-12: 3rem;        /* 48px */
--space-14: 3.5rem;      /* 56px */
--space-16: 4rem;        /* 64px */
--space-20: 5rem;        /* 80px */
--space-24: 6rem;        /* 96px */
--space-28: 7rem;        /* 112px */
--space-32: 8rem;        /* 128px */
--space-36: 9rem;        /* 144px */
--space-40: 10rem;       /* 160px */
--space-44: 11rem;       /* 176px */
--space-48: 12rem;       /* 192px */
--space-52: 13rem;       /* 208px */
--space-56: 14rem;       /* 224px */
--space-60: 15rem;       /* 240px */
--space-64: 16rem;       /* 256px */
```

### Semantic Spacing

```css
/* Component Spacing */
--spacing-component-xs: var(--space-1);    /* 4px */
--spacing-component-sm: var(--space-2);    /* 8px */
--spacing-component-md: var(--space-3);    /* 12px */
--spacing-component-lg: var(--space-4);    /* 16px */
--spacing-component-xl: var(--space-6);    /* 24px */

/* Layout Spacing */
--spacing-layout-xs: var(--space-4);       /* 16px */
--spacing-layout-sm: var(--space-6);       /* 24px */
--spacing-layout-md: var(--space-8);       /* 32px */
--spacing-layout-lg: var(--space-12);      /* 48px */
--spacing-layout-xl: var(--space-16);      /* 64px */
```

---

## Border Radius

```css
--radius-none: 0;
--radius-sm: 0.125rem;    /* 2px */
--radius-default: 0.25rem; /* 4px */
--radius-md: 0.375rem;    /* 6px */
--radius-lg: 0.5rem;      /* 8px */
--radius-xl: 0.75rem;     /* 12px */
--radius-2xl: 1rem;       /* 16px */
--radius-3xl: 1.5rem;     /* 24px */
--radius-full: 9999px;    /* Pill */
```

### Component Radius

```css
--radius-button: var(--radius-md);
--radius-input: var(--radius-md);
--radius-card: var(--radius-lg);
--radius-modal: var(--radius-xl);
--radius-badge: var(--radius-full);
--radius-avatar: var(--radius-full);
```

---

## Shadows

```css
/* Elevation Levels */
--shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);

--shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1),
             0 1px 2px -1px rgba(0, 0, 0, 0.1);

--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
             0 2px 4px -2px rgba(0, 0, 0, 0.1);

--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1),
             0 4px 6px -4px rgba(0, 0, 0, 0.1);

--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1),
             0 8px 10px -6px rgba(0, 0, 0, 0.1);

--shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);

--shadow-inner: inset 0 2px 4px 0 rgba(0, 0, 0, 0.05);

/* Focus Ring */
--shadow-focus: 0 0 0 3px rgba(59, 130, 246, 0.5);
--shadow-focus-error: 0 0 0 3px rgba(239, 68, 68, 0.5);
```

### Component Shadows

```css
--shadow-card: var(--shadow-sm);
--shadow-card-hover: var(--shadow-md);
--shadow-dropdown: var(--shadow-lg);
--shadow-modal: var(--shadow-xl);
--shadow-tooltip: var(--shadow-md);
```

---

## Breakpoints

```css
/* Mobile First Breakpoints */
--breakpoint-sm: 640px;   /* Small tablets */
--breakpoint-md: 768px;   /* Tablets */
--breakpoint-lg: 1024px;  /* Small laptops */
--breakpoint-xl: 1280px;  /* Desktops */
--breakpoint-2xl: 1536px; /* Large screens */
```

### Media Queries

```css
/* Usage */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
@media (min-width: 1536px) { /* 2xl */ }
```

---

## Animation

### Timing Functions

```css
--ease-linear: linear;
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
```

### Duration

```css
--duration-75: 75ms;
--duration-100: 100ms;
--duration-150: 150ms;
--duration-200: 200ms;
--duration-300: 300ms;
--duration-500: 500ms;
--duration-700: 700ms;
--duration-1000: 1000ms;
```

### Semantic Animations

```css
/* Interaction */
--transition-fast: var(--duration-150) var(--ease-out);
--transition-normal: var(--duration-200) var(--ease-out);
--transition-slow: var(--duration-300) var(--ease-out);

/* Enter/Exit */
--transition-enter: var(--duration-200) var(--ease-out);
--transition-exit: var(--duration-150) var(--ease-in);

/* Hover Effects */
--transition-hover: var(--duration-150) var(--ease-out);
```

### Keyframes

```css
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes ping {
  75%, 100% {
    transform: scale(2);
    opacity: 0;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(-25%);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  50% {
    transform: translateY(0);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideInFromRight {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

@keyframes slideInFromBottom {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
```

---

## Component Styles

### Button

```css
/* Base Button */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-body-sm);
  font-weight: var(--font-medium);
  line-height: var(--leading-tight);
  border-radius: var(--radius-button);
  transition: all var(--transition-fast);
  cursor: pointer;
  outline: none;
}

.btn:focus-visible {
  box-shadow: var(--shadow-focus);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Variants */
.btn-primary {
  background: var(--color-primary-500);
  color: var(--text-inverse);
}
.btn-primary:hover {
  background: var(--color-primary-600);
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
}
.btn-secondary:hover {
  background: var(--bg-tertiary);
  border-color: var(--border-hover);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}
.btn-ghost:hover {
  background: var(--bg-tertiary);
}

.btn-danger {
  background: var(--color-error-500);
  color: var(--text-inverse);
}
.btn-danger:hover {
  background: var(--color-error-600);
}

/* Sizes */
.btn-xs { padding: var(--space-1) var(--space-2); font-size: var(--text-body-xs); }
.btn-sm { padding: var(--space-1.5) var(--space-3); font-size: var(--text-body-sm); }
.btn-md { padding: var(--space-2) var(--space-4); font-size: var(--text-body-sm); }
.btn-lg { padding: var(--space-2.5) var(--space-5); font-size: var(--text-body-md); }
.btn-xl { padding: var(--space-3) var(--space-6); font-size: var(--text-body-lg); }
```

### Input

```css
.input {
  display: block;
  width: 100%;
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-body-sm);
  line-height: var(--leading-normal);
  color: var(--text-primary);
  background: var(--bg-primary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-input);
  transition: border-color var(--transition-fast),
              box-shadow var(--transition-fast);
}

.input:hover {
  border-color: var(--border-hover);
}

.input:focus {
  outline: none;
  border-color: var(--border-focus);
  box-shadow: var(--shadow-focus);
}

.input:disabled {
  background: var(--bg-tertiary);
  color: var(--text-disabled);
  cursor: not-allowed;
}

.input-error {
  border-color: var(--color-error-500);
}
.input-error:focus {
  box-shadow: var(--shadow-focus-error);
}
```

### Card

```css
.card {
  background: var(--surface-default);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
}

.card-hover:hover {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-1px);
  transition: all var(--transition-fast);
}

.card-header {
  padding: var(--space-4);
  border-bottom: 1px solid var(--border-default);
}

.card-body {
  padding: var(--space-4);
}

.card-footer {
  padding: var(--space-4);
  border-top: 1px solid var(--border-default);
  background: var(--bg-secondary);
  border-radius: 0 0 var(--radius-card) var(--radius-card);
}
```

### Badge

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-0.5) var(--space-2);
  font-size: var(--text-label-md);
  font-weight: var(--font-medium);
  border-radius: var(--radius-badge);
}

.badge-default {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.badge-success {
  background: var(--color-success-100);
  color: var(--color-success-700);
}

.badge-warning {
  background: var(--color-warning-100);
  color: var(--color-warning-700);
}

.badge-error {
  background: var(--color-error-100);
  color: var(--color-error-700);
}

.badge-info {
  background: var(--color-info-100);
  color: var(--color-info-700);
}

.badge-primary {
  background: var(--color-primary-100);
  color: var(--color-primary-700);
}
```

### Table

```css
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-body-sm);
}

.table th {
  padding: var(--space-3) var(--space-4);
  text-align: left;
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-default);
}

.table td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--border-default);
}

.table tr:hover td {
  background: var(--bg-secondary);
}

.table-striped tr:nth-child(even) td {
  background: var(--bg-secondary);
}
```

### Modal

```css
.modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--bg-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn var(--duration-200) var(--ease-out);
}

.modal {
  background: var(--surface-default);
  border-radius: var(--radius-modal);
  box-shadow: var(--shadow-modal);
  max-width: 90vw;
  max-height: 90vh;
  overflow: hidden;
  animation: scaleIn var(--duration-200) var(--ease-out);
}

.modal-sm { width: 400px; }
.modal-md { width: 560px; }
.modal-lg { width: 720px; }
.modal-xl { width: 960px; }

.modal-header {
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-body {
  padding: var(--space-6);
  overflow-y: auto;
}

.modal-footer {
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--border-default);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}
```

### Status Indicator

```css
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.status-dot-active {
  background: var(--color-success-500);
  box-shadow: 0 0 0 2px var(--color-success-100);
}

.status-dot-idle {
  background: var(--color-secondary-400);
}

.status-dot-stale {
  background: var(--color-warning-500);
  animation: pulse 2s infinite;
}

.status-dot-error {
  background: var(--color-error-500);
}

.status-dot-pending {
  background: var(--color-info-500);
}
```

### Progress Bar

```css
.progress {
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: var(--color-primary-500);
  border-radius: var(--radius-full);
  transition: width var(--duration-300) var(--ease-out);
}

.progress-bar-success { background: var(--color-success-500); }
.progress-bar-warning { background: var(--color-warning-500); }
.progress-bar-error { background: var(--color-error-500); }

.progress-sm { height: 4px; }
.progress-md { height: 8px; }
.progress-lg { height: 12px; }
```

---

## Dark Mode

### Dark Mode Colors

```css
[data-theme="dark"] {
  /* Backgrounds */
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-tertiary: #334155;
  --bg-elevated: #1e293b;
  --bg-overlay: rgba(0, 0, 0, 0.7);

  /* Surfaces */
  --surface-default: #1e293b;
  --surface-raised: #334155;
  --surface-sunken: #0f172a;
  --surface-overlay: #334155;

  /* Text */
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-tertiary: #64748b;
  --text-disabled: #475569;
  --text-inverse: #0f172a;
  --text-link: #60a5fa;
  --text-link-hover: #93c5fd;

  /* Borders */
  --border-default: #334155;
  --border-hover: #475569;
  --border-focus: #60a5fa;

  /* Shadows */
  --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.3),
               0 1px 2px -1px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4),
               0 2px 4px -2px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5),
               0 4px 6px -4px rgba(0, 0, 0, 0.5);

  /* Semantic adjustments */
  --color-success-100: #064e3b;
  --color-success-700: #6ee7b7;
  --color-warning-100: #78350f;
  --color-warning-700: #fcd34d;
  --color-error-100: #7f1d1d;
  --color-error-700: #fca5a5;
  --color-info-100: #164e63;
  --color-info-700: #67e8f9;
  --color-primary-100: #1e3a8a;
  --color-primary-700: #93c5fd;
}
```

### Dark Mode Toggle

```css
/* System preference detection */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    /* Apply dark mode variables */
  }
}

/* Manual toggle */
[data-theme="dark"] {
  /* Apply dark mode variables */
}
```

---

## Design Tokens

### tokens.json (Design Token Format)

```json
{
  "color": {
    "primary": {
      "50": { "value": "#eff6ff", "type": "color" },
      "100": { "value": "#dbeafe", "type": "color" },
      "500": { "value": "#3b82f6", "type": "color" },
      "600": { "value": "#2563eb", "type": "color" },
      "900": { "value": "#1e3a8a", "type": "color" }
    },
    "semantic": {
      "success": { "value": "{color.success.500}", "type": "color" },
      "warning": { "value": "{color.warning.500}", "type": "color" },
      "error": { "value": "{color.error.500}", "type": "color" },
      "info": { "value": "{color.info.500}", "type": "color" }
    },
    "text": {
      "primary": { "value": "#0f172a", "type": "color" },
      "secondary": { "value": "#475569", "type": "color" },
      "tertiary": { "value": "#64748b", "type": "color" }
    }
  },
  "spacing": {
    "1": { "value": "4px", "type": "spacing" },
    "2": { "value": "8px", "type": "spacing" },
    "3": { "value": "12px", "type": "spacing" },
    "4": { "value": "16px", "type": "spacing" },
    "6": { "value": "24px", "type": "spacing" },
    "8": { "value": "32px", "type": "spacing" }
  },
  "typography": {
    "fontFamily": {
      "sans": { "value": "Inter, sans-serif", "type": "fontFamily" },
      "mono": { "value": "JetBrains Mono, monospace", "type": "fontFamily" }
    },
    "fontSize": {
      "xs": { "value": "12px", "type": "fontSize" },
      "sm": { "value": "14px", "type": "fontSize" },
      "md": { "value": "16px", "type": "fontSize" },
      "lg": { "value": "18px", "type": "fontSize" },
      "xl": { "value": "20px", "type": "fontSize" }
    },
    "fontWeight": {
      "normal": { "value": "400", "type": "fontWeight" },
      "medium": { "value": "500", "type": "fontWeight" },
      "semibold": { "value": "600", "type": "fontWeight" },
      "bold": { "value": "700", "type": "fontWeight" }
    }
  },
  "borderRadius": {
    "sm": { "value": "4px", "type": "borderRadius" },
    "md": { "value": "6px", "type": "borderRadius" },
    "lg": { "value": "8px", "type": "borderRadius" },
    "full": { "value": "9999px", "type": "borderRadius" }
  },
  "shadow": {
    "sm": { "value": "0 1px 3px 0 rgba(0,0,0,0.1)", "type": "boxShadow" },
    "md": { "value": "0 4px 6px -1px rgba(0,0,0,0.1)", "type": "boxShadow" },
    "lg": { "value": "0 10px 15px -3px rgba(0,0,0,0.1)", "type": "boxShadow" }
  }
}
```

### Tailwind Config

```javascript
// tailwind.config.js

module.exports = {
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: 'var(--color-primary-50)',
          100: 'var(--color-primary-100)',
          200: 'var(--color-primary-200)',
          300: 'var(--color-primary-300)',
          400: 'var(--color-primary-400)',
          500: 'var(--color-primary-500)',
          600: 'var(--color-primary-600)',
          700: 'var(--color-primary-700)',
          800: 'var(--color-primary-800)',
          900: 'var(--color-primary-900)',
        },
        secondary: {
          // ... same pattern
        },
        success: {
          // ... same pattern
        },
        warning: {
          // ... same pattern
        },
        error: {
          // ... same pattern
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'focus': '0 0 0 3px rgba(59, 130, 246, 0.5)',
        'focus-error': '0 0 0 3px rgba(239, 68, 68, 0.5)',
      },
      animation: {
        'fade-in': 'fadeIn 200ms ease-out',
        'slide-in-right': 'slideInFromRight 300ms ease-out',
        'slide-in-bottom': 'slideInFromBottom 300ms ease-out',
        'scale-in': 'scaleIn 200ms ease-out',
      },
    },
  },
  plugins: [],
};
```

---

## Iconography

### Icon System

- **Library:** Lucide React (MIT licensed)
- **Size Scale:**
  - `xs`: 12px
  - `sm`: 16px
  - `md`: 20px
  - `lg`: 24px
  - `xl`: 32px

### Core Icons

```typescript
// Navigation
import {
  LayoutDashboard,
  Users,
  Briefcase,
  SquareStack,
  MessageSquare,
  Wallet,
  BarChart3,
  Settings,
  LogOut,
} from 'lucide-react';

// Status
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  Loader2,
} from 'lucide-react';

// Actions
import {
  Plus,
  Edit,
  Trash2,
  Copy,
  Download,
  Upload,
  RefreshCw,
  Search,
  Filter,
  MoreHorizontal,
  ChevronDown,
  ChevronRight,
  X,
} from 'lucide-react';

// Data
import {
  Database,
  Server,
  Cpu,
  Zap,
  Activity,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
```

### Icon Component

```typescript
interface IconProps {
  name: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const SIZES = {
  xs: 12,
  sm: 16,
  md: 20,
  lg: 24,
  xl: 32,
};

export function Icon({ name, size = 'md', className }: IconProps) {
  const IconComponent = Icons[name];
  return <IconComponent size={SIZES[size]} className={className} />;
}
```

---

## Document Revision

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-13 | Initial design system skeleton |
