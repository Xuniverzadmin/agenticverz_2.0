# PIN-603: Stagetest Auth Bypass Verification

## Metadata
- Date: 2026-02-21
- Scope: Stagetest frontend auth-bypass verification (route guards + runtime behavior)
- Environment: `https://stagetest.agenticverz.com`
- Verification mode: source audit + live HTTP probes + Playwright browser probe

## Verified Claims

### 1) Stagetest env file exists with bypass enabled
- File: `website/app-shell/.env.stagetest`
- Verified values:
  - `VITE_AUTH_BYPASS=true`
  - `VITE_CLERK_PUBLISHABLE_KEY=pk_test_...`

### 2) Route guard bypass is implemented
- File: `website/app-shell/src/routes/ProtectedRoute.tsx`
  - Early return when `import.meta.env.VITE_AUTH_BYPASS === 'true'`
- File: `website/app-shell/src/routes/FounderRoute.tsx`
  - Same early return in `FounderRoute`
  - Same early return in `CustomerRoute`

### 3) Root redirect is switched to `/stagetest` for bypass builds
- File: `website/app-shell/src/routes/index.tsx`
  - Root index route uses:
    - bypass true -> `/stagetest`
    - bypass false -> `getCatchAllRoute()`
  - Catch-all route uses the same bypass-aware redirect

### 4) Clerk provider remains loaded
- File: `website/app-shell/src/App.tsx`
  - `ClerkAuthSync` remains present.
- File: `website/app-shell/src/main.tsx`
  - `ClerkProvider` remains the app wrapper.

### 5) Stagetest Apache points to stagetest build
- File: `/etc/apache2/sites-available/stagetest.agenticverz.com.conf`
  - `DocumentRoot /root/agenticverz2.0/website/app-shell/dist-stagetest`
- Production isolation check:
  - `/etc/apache2/sites-available/console.agenticverz.com.conf`
  - Still points to `.../dist` (not `dist-stagetest`)

## Runtime Verification Evidence

### HTTP probe (live)
- `GET /` -> `200 text/html`
- `GET /stagetest` -> `200 text/html`
- `GET /login` -> `200 text/html`
- Served root HTML references stagetest bundle:
  - `/assets/index-FhFQYUk8.js`
  - `/assets/index-DVweruq2.css`

### Browser probe (Playwright, headless)
- Navigate to `https://stagetest.agenticverz.com/`
  - Final URL: `https://stagetest.agenticverz.com/stagetest`
  - `data-testid="stagetest-page"` present
  - Login/password form not detected on root navigation

## Conclusion
Stagetest auth bypass is active as designed for evidence browsing. Root navigation lands on `/stagetest` without login gating, while production console routing remains isolated to the normal `dist` build.

