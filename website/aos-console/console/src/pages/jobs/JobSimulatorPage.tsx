import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Play, AlertTriangle, CheckCircle, XCircle, Cpu, Plus, Trash2 } from 'lucide-react';
import { simulate, getSandboxStatus, getDivergenceReport, type SimulationResult } from '@/api/costsim';
import { getSkills, getCapabilities } from '@/api/runtime';
import { Card, CardHeader, CardBody, Button, Input, Select } from '@/components/common';
import { toastSuccess, toastError } from '@/components/common/Toast';
import { formatCredits, formatDuration } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface Step {
  skill: string;
  iterations: number;
}

export default function JobSimulatorPage() {
  const [steps, setSteps] = useState<Step[]>([{ skill: 'llm_invoke', iterations: 1 }]);
  const [budgetCents, setBudgetCents] = useState(1000);
  const [scenario, setScenario] = useState('');
  const [result, setResult] = useState<SimulationResult | null>(null);

  const { data: skills } = useQuery({
    queryKey: ['skills'],
    queryFn: getSkills,
  });

  const { data: capabilities } = useQuery({
    queryKey: ['capabilities'],
    queryFn: getCapabilities,
  });

  const { data: sandboxStatus } = useQuery({
    queryKey: ['sandbox-status'],
    queryFn: getSandboxStatus,
  });

  const { data: divergence } = useQuery({
    queryKey: ['divergence'],
    queryFn: getDivergenceReport,
  });

  const simulateMutation = useMutation({
    mutationFn: () => simulate({
      scenario,
      steps: steps.map(s => ({ skill: s.skill, iterations: s.iterations })),
      budget_cents: budgetCents,
    }),
    onSuccess: (data) => {
      setResult(data);
      toastSuccess('Simulation complete');
    },
    onError: () => {
      toastError('Simulation failed');
    },
  });

  // Build skill options from both endpoints
  const skillList = Array.isArray(skills) && skills.length > 0
    ? skills
    : Object.entries(capabilities?.skills || {}).map(([id]) => ({ id, skill_id: id }));

  const skillOptions = skillList.map((s: { id?: string; skill_id?: string }) => ({
    value: s.id || s.skill_id || '',
    label: s.id || s.skill_id || '',
  }));

  const addStep = () => {
    setSteps([...steps, { skill: 'llm_invoke', iterations: 1 }]);
  };

  const removeStep = (index: number) => {
    setSteps(steps.filter((_, i) => i !== index));
  };

  const updateStep = (index: number, field: keyof Step, value: string | number) => {
    const newSteps = [...steps];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setSteps(newSteps);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            Predictive Simulation
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Cost and feasibility prediction before execution
          </p>
        </div>
        <div className="flex items-center gap-2">
          {sandboxStatus?.status && (
            <span className={cn(
              'px-2 py-1 text-xs rounded-full',
              sandboxStatus.status === 'healthy' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
            )}>
              Sandbox: {sandboxStatus.status}
            </span>
          )}
          {divergence?.divergence !== undefined && (
            <span className={cn(
              'px-2 py-1 text-xs rounded-full',
              divergence.divergence < 0.1 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
            )}>
              Divergence: {(divergence.divergence * 100).toFixed(1)}%
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration Panel */}
        <Card>
          <CardHeader title="Simulation Configuration" />
          <CardBody className="space-y-4">
            <Input
              label="Scenario Description (optional)"
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              placeholder="Describe the execution scenario..."
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Budget (cents): {budgetCents}
              </label>
              <input
                type="range"
                min={100}
                max={10000}
                step={100}
                value={budgetCents}
                onChange={(e) => setBudgetCents(Number(e.target.value))}
                className="w-full"
              />
              <div className="text-xs text-gray-500 mt-1">
                {formatCredits(budgetCents)} credits
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Execution Steps
                </label>
                <Button size="sm" variant="outline" onClick={addStep}>
                  <Plus size={14} className="mr-1" />
                  Add Step
                </Button>
              </div>
              <div className="space-y-3">
                {steps.map((step, index) => (
                  <div key={index} className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span className="text-xs font-medium text-gray-500 w-6">{index + 1}.</span>
                    <Select
                      options={[
                        { value: '', label: 'Select skill...' },
                        ...skillOptions,
                      ]}
                      value={step.skill}
                      onChange={(e) => updateStep(index, 'skill', e.target.value)}
                      className="flex-1"
                    />
                    <Input
                      type="number"
                      min={1}
                      max={100}
                      value={step.iterations}
                      onChange={(e) => updateStep(index, 'iterations', Number(e.target.value))}
                      className="w-20"
                      placeholder="x"
                    />
                    <span className="text-xs text-gray-500">iterations</span>
                    {steps.length > 1 && (
                      <button
                        onClick={() => removeStep(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                onClick={() => simulateMutation.mutate()}
                loading={simulateMutation.isPending}
                disabled={steps.length === 0 || steps.some(s => !s.skill)}
                icon={<Play size={16} />}
              >
                Run Simulation
              </Button>
              <Button variant="secondary" onClick={() => setResult(null)}>
                Clear Results
              </Button>
            </div>
          </CardBody>
        </Card>

        {/* Results Panel */}
        <Card>
          <CardHeader title="Simulation Results" />
          <CardBody>
            {!result ? (
              <div className="text-center py-12 text-gray-500">
                <Cpu className="mx-auto mb-2 text-gray-400" size={32} />
                Configure your execution plan and click Simulate
              </div>
            ) : (
              <div className="space-y-6">
                {/* Feasibility */}
                <div
                  className={cn(
                    'p-4 rounded-lg flex items-center gap-3',
                    result.feasible
                      ? 'bg-green-50 dark:bg-green-900/20'
                      : 'bg-red-50 dark:bg-red-900/20'
                  )}
                >
                  {result.feasible ? (
                    <CheckCircle className="text-green-600" size={24} />
                  ) : (
                    <XCircle className="text-red-600" size={24} />
                  )}
                  <div>
                    <div className="font-semibold">
                      {result.feasible ? 'Feasible' : 'Not Feasible'}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {result.feasible
                        ? 'This execution can proceed'
                        : 'This execution cannot proceed'}
                    </div>
                  </div>
                </div>

                {/* Cost Estimate */}
                <div>
                  <h4 className="font-medium mb-2">Predicted Cost</h4>
                  <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                    <div className="text-2xl font-semibold">
                      {formatCredits(result.estimated_cost_cents || 0)}
                    </div>
                    {result.step_estimates && result.step_estimates.length > 0 && (
                      <div className="text-sm text-gray-500 mt-2 space-y-1">
                        {result.step_estimates.map((s, i) => (
                          <div key={i} className="flex justify-between">
                            <span className="font-mono">{s.skill_id}</span>
                            <span>{formatCredits(s.estimated_cost_cents)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Time Estimate */}
                <div>
                  <h4 className="font-medium mb-2">Predicted Duration</h4>
                  <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                    <div className="text-xl font-semibold">
                      ~{formatDuration((result.estimated_duration_ms || 0) / 1000)}
                    </div>
                    {result.step_estimates && (
                      <div className="text-sm text-gray-500 mt-1">
                        {result.step_estimates.length} step(s)
                      </div>
                    )}
                  </div>
                </div>

                {/* Budget Status */}
                <div>
                  <h4 className="font-medium mb-2">Budget Status</h4>
                  <div
                    className={cn(
                      'p-4 rounded-lg',
                      result.budget_sufficient
                        ? 'bg-green-50 dark:bg-green-900/20'
                        : 'bg-red-50 dark:bg-red-900/20'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span>Remaining: {formatCredits(result.budget_remaining_cents || 0)}</span>
                      <span className={cn(
                        'px-2 py-0.5 text-xs rounded-full',
                        result.budget_sufficient ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      )}>
                        {result.budget_sufficient ? 'Sufficient' : 'Insufficient'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Divergence Risk */}
                {result.divergence_risk !== undefined && (
                  <div>
                    <h4 className="font-medium mb-2">Divergence Risk</h4>
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={cn(
                              'h-full rounded-full',
                              result.divergence_risk < 0.3 ? 'bg-green-500' :
                              result.divergence_risk < 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                            )}
                            style={{ width: `${result.divergence_risk * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium">
                          {(result.divergence_risk * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Warnings */}
                {result.warnings && result.warnings.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Warnings</h4>
                    <div className="space-y-2">
                      {result.warnings.map((warning, i) => (
                        <div
                          key={i}
                          className="flex items-start gap-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg text-sm"
                        >
                          <AlertTriangle className="text-yellow-600 flex-shrink-0" size={16} />
                          <span>{warning}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Incidents */}
                {result.incidents && result.incidents.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Potential Incidents</h4>
                    <div className="space-y-2">
                      {result.incidents.map((incident, i) => (
                        <div
                          key={i}
                          className={cn(
                            'p-3 rounded-lg text-sm',
                            incident.severity === 'high' ? 'bg-red-50 dark:bg-red-900/20' :
                            incident.severity === 'medium' ? 'bg-yellow-50 dark:bg-yellow-900/20' :
                            'bg-gray-50 dark:bg-gray-700/50'
                          )}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-medium">{incident.type}</span>
                            <span className={cn(
                              'text-xs px-2 py-0.5 rounded',
                              incident.severity === 'high' ? 'bg-red-100 text-red-700' :
                              incident.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-gray-100 text-gray-700'
                            )}>
                              {incident.severity}
                            </span>
                          </div>
                          <p className="text-gray-600 dark:text-gray-400 mt-1">{incident.message}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
