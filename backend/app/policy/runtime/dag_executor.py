# M20 Policy Runtime - DAG Executor
# Parallel execution of policy DAG stages
"""
DAG-based executor for PLang v2.0.

Executes policies in topologically sorted order:
- Parallel execution within stages
- Sequential execution across stages
- Governance-aware ordering
- Full execution trace
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.policy.compiler.grammar import ActionType
from app.policy.ir.ir_nodes import IRModule
from app.policy.optimizer.dag_sorter import DAGSorter, ExecutionPlan
from app.policy.runtime.deterministic_engine import (
    DeterministicEngine,
    ExecutionContext,
    ExecutionResult,
)
from app.policy.runtime.intent import Intent


@dataclass
class StageResult:
    """Result of executing a single stage."""

    stage_index: int
    policies_executed: List[str]
    results: Dict[str, ExecutionResult]
    final_action: Optional[ActionType] = None
    intents: List[Intent] = field(default_factory=list)
    duration_steps: int = 0

    @property
    def success(self) -> bool:
        """Check if all policies in stage succeeded."""
        return all(r.success for r in self.results.values())

    @property
    def was_blocked(self) -> bool:
        """Check if execution was blocked by a DENY action."""
        return self.final_action == ActionType.DENY


@dataclass
class ExecutionTrace:
    """Full execution trace across all stages."""

    execution_id: str
    total_stages: int
    stage_results: List[StageResult] = field(default_factory=list)
    final_action: Optional[ActionType] = None
    all_intents: List[Intent] = field(default_factory=list)
    total_steps: int = 0

    # Governance summary
    safety_checks_passed: int = 0
    privacy_checks_passed: int = 0
    operational_checks_passed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for audit logging."""
        return {
            "execution_id": self.execution_id,
            "total_stages": self.total_stages,
            "stages": [
                {
                    "index": sr.stage_index,
                    "policies": sr.policies_executed,
                    "success": sr.success,
                    "action": sr.final_action.value if sr.final_action else None,
                }
                for sr in self.stage_results
            ],
            "final_action": self.final_action.value if self.final_action else None,
            "intents_count": len(self.all_intents),
            "total_steps": self.total_steps,
            "governance_summary": {
                "safety_passed": self.safety_checks_passed,
                "privacy_passed": self.privacy_checks_passed,
                "operational_passed": self.operational_checks_passed,
            },
        }


class DAGExecutor:
    """
    Executes policies in DAG order.

    Features:
    - Parallel execution within stages
    - Early termination on DENY
    - Governance-aware execution order
    - Full audit trail
    """

    def __init__(self, engine: Optional[DeterministicEngine] = None):
        self.engine = engine or DeterministicEngine()
        self.dag_sorter = DAGSorter()

    async def execute(
        self,
        module: IRModule,
        context: ExecutionContext,
        plan: Optional[ExecutionPlan] = None,
    ) -> ExecutionTrace:
        """
        Execute all policies in DAG order.

        Args:
            module: Compiled IR module
            context: Execution context
            plan: Optional pre-computed execution plan

        Returns:
            ExecutionTrace with full audit trail
        """
        # Build execution plan if not provided
        if not plan:
            self.dag_sorter.build_dag(module)
            plan = self.dag_sorter.sort()

        trace = ExecutionTrace(
            execution_id=context.execution_id,
            total_stages=len(plan.stages),
        )

        # Execute stage by stage
        for stage_index, stage_policies in enumerate(plan.stages):
            stage_result = await self._execute_stage(
                stage_index=stage_index,
                policies=stage_policies,
                module=module,
                context=context,
            )

            trace.stage_results.append(stage_result)
            trace.total_steps += stage_result.duration_steps
            trace.all_intents.extend(stage_result.intents)

            # Update governance counters
            for policy_name, result in stage_result.results.items():
                func = module.get_function(policy_name)
                if func and func.governance:
                    cat = func.governance.category.value
                    if cat == "SAFETY" and result.success:
                        trace.safety_checks_passed += 1
                    elif cat == "PRIVACY" and result.success:
                        trace.privacy_checks_passed += 1
                    elif cat == "OPERATIONAL" and result.success:
                        trace.operational_checks_passed += 1

            # Early termination on DENY
            if stage_result.was_blocked:
                trace.final_action = ActionType.DENY
                break

            # Update final action (most restrictive wins)
            if stage_result.final_action:
                if trace.final_action is None:
                    trace.final_action = stage_result.final_action
                elif self._is_more_restrictive(stage_result.final_action, trace.final_action):
                    trace.final_action = stage_result.final_action

        # Default to ALLOW if no action was taken
        if trace.final_action is None:
            trace.final_action = ActionType.ALLOW

        return trace

    async def _execute_stage(
        self,
        stage_index: int,
        policies: List[str],
        module: IRModule,
        context: ExecutionContext,
    ) -> StageResult:
        """
        Execute a single stage (potentially in parallel).

        Args:
            stage_index: Index of this stage
            policies: List of policy names to execute
            module: IR module
            context: Execution context

        Returns:
            StageResult with all policy results
        """
        result = StageResult(
            stage_index=stage_index,
            policies_executed=policies,
            results={},
        )

        if len(policies) == 1:
            # Single policy - execute directly
            policy_name = policies[0]
            exec_result = await self.engine.execute(
                module=module,
                context=context,
                entry_function=policy_name,
            )
            result.results[policy_name] = exec_result
            result.duration_steps = exec_result.step_count
            result.intents = exec_result.intents

            if exec_result.action:
                result.final_action = exec_result.action

        else:
            # Multiple policies - execute in parallel
            tasks = []
            for policy_name in policies:
                # Create a copy of context for parallel execution
                policy_context = ExecutionContext(
                    request_id=context.request_id,
                    user_id=context.user_id,
                    agent_id=context.agent_id,
                    variables=dict(context.variables),
                    max_steps=context.max_steps,
                )
                tasks.append(self._execute_policy(policy_name, module, policy_context))

            # Wait for all to complete
            parallel_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect results
            most_restrictive_action: Optional[ActionType] = None

            for policy_name, exec_result in zip(policies, parallel_results):
                if isinstance(exec_result, Exception):
                    result.results[policy_name] = ExecutionResult(
                        success=False,
                        error=str(exec_result),
                    )
                else:
                    result.results[policy_name] = exec_result
                    result.duration_steps = max(result.duration_steps, exec_result.step_count)
                    result.intents.extend(exec_result.intents)

                    if exec_result.action:
                        if most_restrictive_action is None:
                            most_restrictive_action = exec_result.action
                        elif self._is_more_restrictive(exec_result.action, most_restrictive_action):
                            most_restrictive_action = exec_result.action

            result.final_action = most_restrictive_action

        return result

    async def _execute_policy(
        self,
        policy_name: str,
        module: IRModule,
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Execute a single policy."""
        return await self.engine.execute(
            module=module,
            context=context,
            entry_function=policy_name,
        )

    def _is_more_restrictive(self, action: ActionType, compared_to: ActionType) -> bool:
        """Check if an action is more restrictive than another."""
        precedence = {
            ActionType.DENY: 100,
            ActionType.ESCALATE: 80,
            ActionType.ROUTE: 50,
            ActionType.ALLOW: 10,
        }
        return precedence.get(action, 0) > precedence.get(compared_to, 0)

    def get_execution_plan(self, module: IRModule) -> ExecutionPlan:
        """
        Get the execution plan for a module.

        Args:
            module: IR module to plan

        Returns:
            ExecutionPlan with stages and ordering
        """
        self.dag_sorter.build_dag(module)
        return self.dag_sorter.sort()

    def visualize_plan(self, module: IRModule) -> str:
        """
        Get a visual representation of the execution plan.

        Args:
            module: IR module to visualize

        Returns:
            ASCII visualization of the DAG
        """
        self.dag_sorter.build_dag(module)
        return self.dag_sorter.visualize()
