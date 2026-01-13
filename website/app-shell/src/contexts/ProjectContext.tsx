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
 * - Switching Projects changes data scope only, not:
 *   - Domains
 *   - Sidebar structure
 *   - Topics
 *   - Order semantics
 * - Cross-project aggregation is FORBIDDEN in Customer Console
 *
 * NOT L2.1 — This is Global Context, not Projection
 */

/**
 * ProjectContext - Global Project Scope Selector
 *
 * RULE-AUTH-UI-001: Clerk is the auth store
 * - Use useAuth() for authentication state
 * - Keep tenantId in authStore (app-specific state)
 *
 * Reference: PIN-407, docs/architecture/FRONTEND_AUTH_CONTRACT.md
 */
import React, { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { useAuthStore } from '@/stores/authStore';

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
// Demo Projects (Replace with API call in production)
// ============================================================================

const DEMO_PROJECTS: Project[] = [
  {
    id: 'proj_default',
    name: 'Default Project',
    description: 'Main project workspace',
    isDefault: true,
  },
  {
    id: 'proj_staging',
    name: 'Staging',
    description: 'Pre-production testing',
  },
  {
    id: 'proj_experiments',
    name: 'Experiments',
    description: 'Experimental agents',
  },
];

// ============================================================================
// Context
// ============================================================================

const ProjectContext = createContext<ProjectContextValue | null>(null);

// ============================================================================
// Storage Keys
// ============================================================================

const PROJECT_STORAGE_KEY = 'aos-selected-project';

// ============================================================================
// Provider
// ============================================================================

interface ProjectProviderProps {
  children: ReactNode;
}

export function ProjectProvider({ children }: ProjectProviderProps) {
  // Use Clerk for auth status, authStore for tenantId (app-specific)
  const { isSignedIn } = useAuth();
  const { tenantId } = useAuthStore();

  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load projects on mount / auth change
  useEffect(() => {
    async function loadProjects() {
      setIsLoading(true);
      setError(null);

      try {
        // TODO: Replace with actual API call
        // const response = await fetch(`/api/v1/projects?tenant_id=${tenantId}`);
        // const data = await response.json();
        // setProjects(data.projects);

        // For now, use demo projects
        await new Promise(resolve => setTimeout(resolve, 100)); // Simulate network
        setProjects(DEMO_PROJECTS);

        // Restore selected project from storage
        const storedProjectId = localStorage.getItem(PROJECT_STORAGE_KEY);
        const storedProject = DEMO_PROJECTS.find(p => p.id === storedProjectId);
        const defaultProject = DEMO_PROJECTS.find(p => p.isDefault) || DEMO_PROJECTS[0];

        setCurrentProject(storedProject || defaultProject || null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load projects');
      } finally {
        setIsLoading(false);
      }
    }

    if (isSignedIn) {
      loadProjects();
    } else {
      setProjects([]);
      setCurrentProject(null);
      setIsLoading(false);
    }
  }, [isSignedIn, tenantId]);

  // Select project handler
  const selectProject = useCallback((projectId: string) => {
    const project = projects.find(p => p.id === projectId);
    if (project) {
      setCurrentProject(project);
      localStorage.setItem(PROJECT_STORAGE_KEY, projectId);
    }
  }, [projects]);

  const value: ProjectContextValue = {
    currentProject,
    projects,
    selectProject,
    isLoading,
    error,
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
    // Return safe defaults if no provider (e.g., during SSR or tests)
    return {
      currentProject: null,
      projects: [],
      selectProject: () => {},
      isLoading: false,
      error: null,
    };
  }

  return context;
}

// ============================================================================
// Export for App.tsx / Layout
// ============================================================================

export { ProjectContext };
