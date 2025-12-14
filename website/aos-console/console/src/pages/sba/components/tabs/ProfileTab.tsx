// ProfileTab Component
// M16 - Shows agent purpose, permissions, tasks, and completion score

import type { SBAAgent } from '@/types/sba';
import { PurposeCard } from '../profile/PurposeCard';
import { PermissionsPanel } from '../profile/PermissionsPanel';
import { TaskChecklist } from '../profile/TaskChecklist';
import { CompletionScore } from '../profile/CompletionScore';

interface ProfileTabProps {
  agent: SBAAgent;
}

export function ProfileTab({ agent }: ProfileTabProps) {
  const sba = agent.sba;

  // Extract data from SBA schema
  const purpose = sba?.winning_aspiration?.description || '';
  const domains = sba?.where_to_play?.domain ? [sba.where_to_play.domain] : [];
  const tools = sba?.where_to_play?.allowed_tools || [];
  const contexts = sba?.where_to_play?.allowed_contexts || [];

  // Build limits from env
  const limits = sba?.capabilities_capacity?.env ? {
    memory: sba.capabilities_capacity.env.memory,
    timeout: sba.capabilities_capacity.env.timeout_seconds
      ? `${sba.capabilities_capacity.env.timeout_seconds}s`
      : undefined,
    budget: sba.capabilities_capacity.env.budget_tokens,
  } : undefined;

  // Build tasks from how_to_win
  const tasks = (sba?.how_to_win?.tasks || []).map((task, i) => ({
    name: task,
    done: false, // Would come from execution state
  }));

  // Build tests from how_to_win
  const tests = (sba?.how_to_win?.tests || []).map((test) => ({
    name: test,
    passed: null as boolean | null, // Would come from test results
  }));

  // Calculate completion score
  const fulfillment = sba?.how_to_win?.fulfillment_metric || 0;
  const completionValue = Math.round(fulfillment * 100);

  // Build breakdown (would come from detailed metrics)
  const breakdown = {
    tasks: tasks.length > 0 ? Math.round((tasks.filter(t => t.done).length / tasks.length) * 100) : 0,
    tests: tests.length > 0 ? Math.round((tests.filter(t => t.passed).length / tests.length) * 100) : 0,
    criteria: completionValue,
    system: completionValue,
  };

  return (
    <div className="space-y-4">
      {/* Purpose */}
      <PurposeCard
        description={purpose}
        alignment={fulfillment}
      />

      {/* Permissions */}
      <PermissionsPanel
        domains={domains}
        tools={tools}
        contexts={contexts}
        limits={limits}
        violations={[]}
      />

      {/* Tasks & Tests */}
      <TaskChecklist
        tasks={tasks}
        tests={tests}
      />

      {/* Completion Score */}
      <CompletionScore
        value={completionValue}
        breakdown={breakdown}
        threshold={80}
      />
    </div>
  );
}
