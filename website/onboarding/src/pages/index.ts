/**
 * Onboarding Pages
 *
 * Responsibility: Pre-console tenant setup flow
 *
 * Flow:
 * 1. ConnectPage   - API connection setup (validates credentials)
 * 2. SafetyPage    - Safety policy configuration (guardrails, limits)
 * 3. AlertsPage    - Alert channel configuration (email, Slack, webhook)
 * 4. VerifyPage    - Final verification step (test run)
 * 5. CompletePage  - Completion acknowledgment (marks onboarding complete)
 *
 * Guard: OnboardingRoute (requires auth, NOT completed onboarding)
 * On complete: Sets onboardingComplete=true, redirects to /guard
 *
 * Consumed by: app-shell routes
 * Uses: @/ imports for shared infrastructure (authStore, Toast)
 */

export { default as OnboardingLayout } from './OnboardingLayout';
export { default as ConnectPage } from './ConnectPage';
export { default as SafetyPage } from './SafetyPage';
export { default as AlertsPage } from './AlertsPage';
export { default as VerifyPage } from './VerifyPage';
export { default as CompletePage } from './CompletePage';
