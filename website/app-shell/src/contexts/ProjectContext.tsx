/**
 * ProjectContext - Global Project Scope Selector
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: user action
 *   Execution: sync
 * Role: Provide global project scope for data filtering
 * Reference: PIN-358 Task Group A, PIN-234 Section 5.4
 *
 * GOVERNANCE RULES (Constitution v1.1.0):
 * - Projects are global scope selectors (in header, NOT sidebar)
 * - Projects are NOT domains and must not appear in primary sidebar
 * - Switching Projects changes data scope only
 * - Cross-project aggregation is FORBIDDEN in Customer Console
 *
 * STATUS: DISABLED - No backend API exists.
 * When /api/v1/projects is implemented, wire it here.
 * Until then, this context returns empty state.
 */

import React, { createContext, useContext, ReactNode } from 'react';

// ============================================================================
// Types
// ============================================================================

export interface Project {
  id: string;
  name: string;
  description?: string;
  isDefault?: boolean;
}

export interface ProjectContextValue {
  /** Currently selected project */
  currentProject: Project | null;
  /** All available projects */
  projects: Project[];
  /** Select a different project */
  selectProject: (projectId: string) => void;
  /** Is project data loading */
  isLoading: boolean;
  /** Error if project load failed */
  error: string | null;
}

// ============================================================================
// Context
// ============================================================================

const ProjectContext = createContext<ProjectContextValue | null>(null);

// ============================================================================
// Provider — DISABLED (No Backend API)
// ============================================================================

interface ProjectProviderProps {
  children: ReactNode;
}

/**
 * ProjectProvider is currently DISABLED.
 *
 * No demo data. No fake projects. No simulated network.
 * When /api/v1/projects exists, implement real fetching here.
 */
export function ProjectProvider({ children }: ProjectProviderProps) {
  // DISABLED: No backend API exists for projects.
  // Returns empty state until real API is wired.
  const value: ProjectContextValue = {
    currentProject: null,
    projects: [],
    selectProject: () => {
      console.warn('[ProjectContext] Projects API not implemented. Cannot select project.');
    },
    isLoading: false,
    error: 'Projects API not implemented',
  };

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

export function useProject(): ProjectContextValue {
  const context = useContext(ProjectContext);

  if (!context) {
    return {
      currentProject: null,
      projects: [],
      selectProject: () => {
        console.warn('[ProjectContext] No ProjectProvider. Cannot select project.');
      },
      isLoading: false,
      error: 'No ProjectProvider',
    };
  }

  return context;
}

// ============================================================================
// Export for App.tsx / Layout
// ============================================================================

export { ProjectContext };
