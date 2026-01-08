/**
 * ProjectSelector - Global Project Scope Dropdown
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: user action
 *   Execution: sync
 * Role: Allow user to switch project scope
 * Reference: PIN-358 Task Group A
 *
 * PLACEMENT: Header (global, NOT sidebar)
 * DATA SOURCE: ProjectContext (NOT L2.1, NOT projection)
 */

import { ChevronDown, Folder, Check, Loader2 } from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { cn } from '@/lib/utils';
import { useProject } from '@/contexts/ProjectContext';

export function ProjectSelector() {
  const { currentProject, projects, selectProject, isLoading, error } = useProject();

  // Don't render if no projects or loading
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 text-gray-500">
        <Loader2 size={14} className="animate-spin" />
        <span className="text-sm">Loading...</span>
      </div>
    );
  }

  if (error || projects.length === 0) {
    return null;
  }

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors',
          'bg-gray-700/50 text-gray-300 hover:bg-gray-700 focus:outline-none'
        )}>
          <Folder size={14} className="text-gray-400" />
          <span className="text-sm font-medium max-w-[140px] truncate">
            {currentProject?.name || 'Select Project'}
          </span>
          <ChevronDown size={14} className="text-gray-500" />
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          className="min-w-[200px] bg-gray-800 rounded-lg shadow-lg border border-gray-700 py-2 z-50"
          sideOffset={8}
          align="start"
        >
          <div className="px-3 py-1.5 mb-1">
            <span className="text-xs text-gray-500 uppercase tracking-wider">
              Project Scope
            </span>
          </div>

          {projects.map((project) => {
            const isSelected = project.id === currentProject?.id;

            return (
              <DropdownMenu.Item
                key={project.id}
                className={cn(
                  'flex items-start gap-3 px-3 py-2 text-sm outline-none cursor-pointer',
                  isSelected
                    ? 'bg-primary-900/30 text-primary-300'
                    : 'text-gray-300 hover:bg-gray-700'
                )}
                onClick={() => selectProject(project.id)}
              >
                <Folder size={16} className={cn(
                  'mt-0.5 flex-shrink-0',
                  isSelected ? 'text-primary-400' : 'text-gray-500'
                )} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{project.name}</span>
                    {project.isDefault && (
                      <span className="text-xs px-1 py-0.5 bg-gray-700 text-gray-400 rounded">
                        default
                      </span>
                    )}
                  </div>
                  {project.description && (
                    <span className="text-xs text-gray-500 line-clamp-1">
                      {project.description}
                    </span>
                  )}
                </div>
                {isSelected && (
                  <Check size={14} className="mt-0.5 text-primary-400" />
                )}
              </DropdownMenu.Item>
            );
          })}

          <DropdownMenu.Separator className="h-px bg-gray-700 my-2" />

          <div className="px-3 py-1 text-xs text-gray-500">
            Data scope: {currentProject?.id || 'none'}
          </div>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}

export default ProjectSelector;
