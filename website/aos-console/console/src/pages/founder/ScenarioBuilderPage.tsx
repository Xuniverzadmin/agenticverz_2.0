/**
 * Scenario Builder Page
 *
 * H2 Cost Simulation v1 - Scenario-based cost projections
 *
 * Features:
 * - Template selection for quick starts
 * - Custom scenario builder with plan steps
 * - Real-time simulation preview
 * - Cost breakdown visualization
 *
 * INVARIANTS:
 * - Advisory ONLY - no real budget changes
 * - Pure computation - no side effects
 * - No action buttons that trigger real operations
 * - Results are informational only
 *
 * Reference: Phase H2 - Cost Simulation v1
 */

import React, { useState, useCallback, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Calculator,
  Play,
  Plus,
  Trash2,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info,
  Clock,
  DollarSign,
  Loader2,
  Copy,
  ChevronRight,
  Zap,
  TrendingUp,
} from 'lucide-react';
import {
  listScenarios,
  createScenario,
  deleteScenario,
  simulateScenario,
  simulateAdhoc,
  formatCost,
  formatDuration,
  getStatusColor,
  getRiskSeverityColor,
  getUtilizationColor,
  Scenario,
  SimulationResult,
  SimulationStepInput,
  AdhocSimulationRequest,
} from '../../api/scenarios';

// =============================================================================
// Available Skills (for scenario builder)
// =============================================================================

const AVAILABLE_SKILLS = [
  { id: 'api_call', name: 'API Call', description: 'External API invocation' },
  { id: 'data_fetch', name: 'Data Fetch', description: 'Retrieve data from storage' },
  { id: 'data_store', name: 'Data Store', description: 'Persist data to storage' },
  { id: 'llm_call', name: 'LLM Call', description: 'Language model inference' },
  { id: 'batch_process', name: 'Batch Process', description: 'Process items in bulk' },
];

// =============================================================================
// Step Editor Component
// =============================================================================

interface StepEditorProps {
  step: SimulationStepInput;
  index: number;
  onChange: (index: number, step: SimulationStepInput) => void;
  onRemove: (index: number) => void;
}

function StepEditor({ step, index, onChange, onRemove }: StepEditorProps) {
  return (
    <div className="bg-gray-900/50 border border-navy-border rounded-lg p-3 mb-2">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-400">Step {index + 1}</span>
        <button
          onClick={() => onRemove(index)}
          className="p-1 hover:bg-red-900/30 rounded text-red-400"
          title="Remove step"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Skill</label>
          <select
            value={step.skill}
            onChange={(e) => onChange(index, { ...step, skill: e.target.value })}
            className="w-full bg-gray-800 border border-navy-border rounded px-2 py-1 text-sm text-white"
          >
            {AVAILABLE_SKILLS.map((skill) => (
              <option key={skill.id} value={skill.id}>
                {skill.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs text-gray-500 mb-1 block">Iterations</label>
          <input
            type="number"
            value={step.iterations || 1}
            onChange={(e) =>
              onChange(index, { ...step, iterations: Math.max(1, parseInt(e.target.value) || 1) })
            }
            min={1}
            max={100}
            className="w-full bg-gray-800 border border-navy-border rounded px-2 py-1 text-sm text-white"
          />
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Simulation Result Display Component
// =============================================================================

interface SimulationResultDisplayProps {
  result: SimulationResult;
}

function SimulationResultDisplay({ result }: SimulationResultDisplayProps) {
  return (
    <div className="space-y-4">
      {/* Status Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {result.feasible ? (
            <CheckCircle className="w-6 h-6 text-green-500" />
          ) : (
            <XCircle className="w-6 h-6 text-red-500" />
          )}
          <div>
            <h3 className={`text-lg font-medium ${getStatusColor(result.status)}`}>
              {result.feasible ? 'Feasible' : 'Budget Exceeded'}
            </h3>
            <p className="text-sm text-gray-400">
              Confidence: {(result.confidence_score * 100).toFixed(1)}%
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-white">
            {formatCost(result.estimated_cost_cents)}
          </div>
          <div className="text-sm text-gray-400">
            of {formatCost(result.budget_cents)} budget
          </div>
        </div>
      </div>

      {/* Budget Utilization Bar */}
      <div>
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-400">Budget Utilization</span>
          <span className={getUtilizationColor(result.budget_utilization_pct)}>
            {result.budget_utilization_pct.toFixed(1)}%
          </span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all ${
              result.budget_utilization_pct >= 90
                ? 'bg-red-500'
                : result.budget_utilization_pct >= 70
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(100, result.budget_utilization_pct)}%` }}
          />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-900/30 rounded-lg p-3 text-center">
          <DollarSign className="w-5 h-5 mx-auto text-green-400 mb-1" />
          <div className="text-lg font-medium text-white">
            {formatCost(result.budget_remaining_cents)}
          </div>
          <div className="text-xs text-gray-400">Remaining</div>
        </div>
        <div className="bg-gray-900/30 rounded-lg p-3 text-center">
          <Clock className="w-5 h-5 mx-auto text-blue-400 mb-1" />
          <div className="text-lg font-medium text-white">
            {formatDuration(result.estimated_duration_ms)}
          </div>
          <div className="text-xs text-gray-400">Duration</div>
        </div>
        <div className="bg-gray-900/30 rounded-lg p-3 text-center">
          <Zap className="w-5 h-5 mx-auto text-yellow-400 mb-1" />
          <div className="text-lg font-medium text-white">
            {result.step_estimates.length}
          </div>
          <div className="text-xs text-gray-400">Steps</div>
        </div>
      </div>

      {/* Step Breakdown */}
      <div>
        <h4 className="text-sm font-medium text-gray-400 mb-2">Step Breakdown</h4>
        <div className="space-y-2">
          {result.step_estimates.map((step) => (
            <div
              key={step.step_index}
              className="flex items-center justify-between bg-gray-900/30 rounded px-3 py-2"
            >
              <div className="flex items-center gap-2">
                <span className="text-xs bg-gray-700 rounded px-2 py-0.5">
                  #{step.step_index + 1}
                </span>
                <span className="text-white text-sm">{step.skill_id}</span>
                <span className="text-gray-500 text-xs">x{step.iterations}</span>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <span className="text-gray-400">
                  {formatDuration(step.latency_ms)}
                </span>
                <span className="text-green-400 font-medium">
                  {formatCost(step.cost_cents)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Warnings */}
      {result.warnings.length > 0 && (
        <div className="bg-yellow-900/20 border border-yellow-800 rounded-lg p-3">
          <h4 className="text-sm font-medium text-yellow-400 mb-2 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Warnings
          </h4>
          <ul className="text-sm text-yellow-300 space-y-1">
            {result.warnings.map((warning, idx) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Risks */}
      {result.risks.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-400">Identified Risks</h4>
          {result.risks.map((risk, idx) => (
            <div
              key={idx}
              className={`rounded-lg px-3 py-2 ${getRiskSeverityColor(risk.severity)}`}
            >
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium uppercase">{risk.severity}</span>
                <span className="text-sm">{risk.message}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Advisory Notice */}
      <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-3 flex items-start gap-2">
        <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
        <div className="text-sm text-blue-300">
          <strong>Advisory Only:</strong> {result.note}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Scenario Card Component
// =============================================================================

interface ScenarioCardProps {
  scenario: Scenario;
  onSelect: (scenario: Scenario) => void;
  onDelete: (scenarioId: string) => void;
}

function ScenarioCard({ scenario, onSelect, onDelete }: ScenarioCardProps) {
  return (
    <div
      className="bg-gray-900/50 border border-navy-border hover:border-blue-600 rounded-lg p-4 cursor-pointer transition-all"
      onClick={() => onSelect(scenario)}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <h3 className="text-white font-medium">{scenario.name}</h3>
          {scenario.is_template && (
            <span className="text-xs bg-blue-900/30 text-blue-400 px-2 py-0.5 rounded">
              Template
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">
            {formatCost(scenario.budget_cents)}
          </span>
          <ChevronRight className="w-4 h-4 text-gray-500" />
        </div>
      </div>
      {scenario.description && (
        <p className="text-sm text-gray-400 mb-2">{scenario.description}</p>
      )}
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500">
          {scenario.plan.length} step{scenario.plan.length !== 1 ? 's' : ''}
        </span>
        {!scenario.is_template && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(scenario.id);
            }}
            className="text-xs text-red-400 hover:text-red-300"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function ScenarioBuilderPage() {
  const queryClient = useQueryClient();

  // State
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
  const [customSteps, setCustomSteps] = useState<SimulationStepInput[]>([
    { skill: 'api_call', params: {}, iterations: 1 },
  ]);
  const [customBudget, setCustomBudget] = useState(1000);
  const [customName, setCustomName] = useState('');
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [isCustomMode, setIsCustomMode] = useState(false);

  // Queries
  const { data: scenarios, isLoading: scenariosLoading } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => listScenarios(true),
  });

  // Mutations
  const simulateMutation = useMutation({
    mutationFn: async () => {
      if (selectedScenario) {
        return simulateScenario(selectedScenario.id);
      } else {
        return simulateAdhoc({ plan: customSteps, budget_cents: customBudget });
      }
    },
    onSuccess: (result) => {
      setSimulationResult(result);
    },
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      return createScenario({
        name: customName || `Custom Scenario ${Date.now()}`,
        plan: customSteps,
        budget_cents: customBudget,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scenarios'] });
      setCustomName('');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteScenario,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scenarios'] });
      setSelectedScenario(null);
    },
  });

  // Handlers
  const handleStepChange = useCallback((index: number, step: SimulationStepInput) => {
    setCustomSteps((prev) => {
      const next = [...prev];
      next[index] = step;
      return next;
    });
    setSimulationResult(null);
  }, []);

  const handleStepRemove = useCallback((index: number) => {
    setCustomSteps((prev) => prev.filter((_, i) => i !== index));
    setSimulationResult(null);
  }, []);

  const handleAddStep = useCallback(() => {
    setCustomSteps((prev) => [...prev, { skill: 'api_call', params: {}, iterations: 1 }]);
    setSimulationResult(null);
  }, []);

  const handleSelectScenario = useCallback((scenario: Scenario) => {
    setSelectedScenario(scenario);
    setIsCustomMode(false);
    setSimulationResult(null);
  }, []);

  const handleStartCustom = useCallback(() => {
    setSelectedScenario(null);
    setIsCustomMode(true);
    setSimulationResult(null);
  }, []);

  const handleCopyFromScenario = useCallback(() => {
    if (selectedScenario) {
      setCustomSteps([...selectedScenario.plan]);
      setCustomBudget(selectedScenario.budget_cents);
      setSelectedScenario(null);
      setIsCustomMode(true);
    }
  }, [selectedScenario]);

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
          <Calculator className="w-7 h-7 text-blue-400" />
          Scenario Builder
        </h1>
        <p className="text-gray-400">
          Build and simulate cost scenarios. All simulations are advisory only - no real budget changes occur.
        </p>
      </div>

      {/* Advisory Banner */}
      <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-3 mb-6 flex items-center gap-3">
        <Info className="w-5 h-5 text-blue-400 flex-shrink-0" />
        <div>
          <span className="text-blue-300 font-medium">Advisory Mode</span>
          <span className="text-blue-400 ml-2 text-sm">
            Simulations are pure computations. No budgets are modified, no operations are triggered.
          </span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left Panel: Scenario Selection */}
        <div className="col-span-1">
          <div className="bg-gray-900/30 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-white font-medium">Scenarios</h2>
              <button
                onClick={handleStartCustom}
                className="flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300"
              >
                <Plus className="w-4 h-4" />
                Custom
              </button>
            </div>

            {scenariosLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
              </div>
            ) : (
              <div className="space-y-3">
                {scenarios?.map((scenario) => (
                  <ScenarioCard
                    key={scenario.id}
                    scenario={scenario}
                    onSelect={handleSelectScenario}
                    onDelete={(id) => deleteMutation.mutate(id)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Center Panel: Editor */}
        <div className="col-span-1">
          <div className="bg-gray-900/30 rounded-lg p-4">
            <h2 className="text-white font-medium mb-4">
              {isCustomMode
                ? 'Custom Scenario'
                : selectedScenario
                  ? selectedScenario.name
                  : 'Select a Scenario'}
            </h2>

            {/* Selected Scenario View */}
            {selectedScenario && !isCustomMode && (
              <div>
                {selectedScenario.description && (
                  <p className="text-gray-400 text-sm mb-4">{selectedScenario.description}</p>
                )}

                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-400">Budget</span>
                    <span className="text-white font-medium">
                      {formatCost(selectedScenario.budget_cents)}
                    </span>
                  </div>
                </div>

                <div className="mb-4">
                  <h4 className="text-sm text-gray-400 mb-2">Plan Steps</h4>
                  {selectedScenario.plan.map((step, idx) => (
                    <div
                      key={idx}
                      className="bg-gray-800 rounded px-3 py-2 mb-2 flex items-center justify-between"
                    >
                      <div>
                        <span className="text-white">{step.skill}</span>
                        <span className="text-gray-500 text-sm ml-2">
                          x{step.iterations || 1}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => simulateMutation.mutate()}
                    disabled={simulateMutation.isPending}
                    className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-4 py-2 rounded"
                  >
                    {simulateMutation.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                    Simulate
                  </button>
                  <button
                    onClick={handleCopyFromScenario}
                    className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded"
                    title="Copy to custom"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Custom Mode Editor */}
            {isCustomMode && (
              <div>
                <div className="mb-4">
                  <label className="text-sm text-gray-400 mb-1 block">Scenario Name</label>
                  <input
                    type="text"
                    value={customName}
                    onChange={(e) => setCustomName(e.target.value)}
                    placeholder="Optional name for saving"
                    className="w-full bg-gray-800 border border-navy-border rounded px-3 py-2 text-sm text-white"
                  />
                </div>

                <div className="mb-4">
                  <label className="text-sm text-gray-400 mb-1 block">Budget (cents)</label>
                  <input
                    type="number"
                    value={customBudget}
                    onChange={(e) => {
                      setCustomBudget(Math.max(0, parseInt(e.target.value) || 0));
                      setSimulationResult(null);
                    }}
                    min={0}
                    max={1000000}
                    className="w-full bg-gray-800 border border-navy-border rounded px-3 py-2 text-sm text-white"
                  />
                </div>

                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm text-gray-400">Plan Steps</label>
                    <button
                      onClick={handleAddStep}
                      className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" />
                      Add Step
                    </button>
                  </div>

                  {customSteps.map((step, idx) => (
                    <StepEditor
                      key={idx}
                      step={step}
                      index={idx}
                      onChange={handleStepChange}
                      onRemove={handleStepRemove}
                    />
                  ))}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => simulateMutation.mutate()}
                    disabled={simulateMutation.isPending || customSteps.length === 0}
                    className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-4 py-2 rounded"
                  >
                    {simulateMutation.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                    Simulate
                  </button>
                  <button
                    onClick={() => createMutation.mutate()}
                    disabled={createMutation.isPending || customSteps.length === 0}
                    className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white px-4 py-2 rounded"
                    title="Save scenario"
                  >
                    {createMutation.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Plus className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Empty State */}
            {!selectedScenario && !isCustomMode && (
              <div className="text-center py-8">
                <Calculator className="w-12 h-12 mx-auto text-gray-600 mb-3" />
                <p className="text-gray-400">
                  Select a scenario from the list or create a custom one
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: Results */}
        <div className="col-span-1">
          <div className="bg-gray-900/30 rounded-lg p-4">
            <h2 className="text-white font-medium mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-400" />
              Simulation Results
            </h2>

            {simulateMutation.isPending && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              </div>
            )}

            {simulateMutation.isError && (
              <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 text-center">
                <AlertTriangle className="w-8 h-8 mx-auto text-red-500" />
                <p className="text-red-400 mt-2">Simulation failed</p>
              </div>
            )}

            {simulationResult && !simulateMutation.isPending && (
              <SimulationResultDisplay result={simulationResult} />
            )}

            {!simulationResult && !simulateMutation.isPending && !simulateMutation.isError && (
              <div className="text-center py-8">
                <Play className="w-12 h-12 mx-auto text-gray-600 mb-3" />
                <p className="text-gray-400">
                  Run a simulation to see cost projections
                </p>
                <p className="text-gray-500 text-sm mt-2">
                  Results are advisory only
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
