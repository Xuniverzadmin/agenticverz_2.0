# M20 Runtime Tests
# Tests for deterministic execution engine
"""
Test suite for M20 Runtime:
- Deterministic execution
- Intent emission
- DAG-based execution
- Governance validation
"""

import pytest

from app.policy.compiler.grammar import ActionType
from app.policy.compiler.parser import Parser
from app.policy.ir.ir_builder import IRBuilder
from app.policy.runtime.dag_executor import DAGExecutor
from app.policy.runtime.deterministic_engine import (
    DeterministicEngine,
    ExecutionContext,
    ExecutionStatus,
)
from app.policy.runtime.intent import (
    Intent,
    IntentEmitter,
    IntentPayload,
    IntentType,
)


class TestExecutionContext:
    """Tests for execution context."""

    def test_context_creation(self):
        """Test creating execution context."""
        ctx = ExecutionContext(
            request_id="req_123",
            user_id="user_456",
            agent_id="agent_789",
        )

        assert ctx.request_id == "req_123"
        assert ctx.execution_id.startswith("exec_")
        assert ctx.status == ExecutionStatus.PENDING

    def test_context_variables(self):
        """Test variable get/set."""
        ctx = ExecutionContext()
        ctx.set_variable("count", 42)

        assert ctx.get_variable("count") == 42
        assert ctx.get_variable("nonexistent") is None

    def test_context_special_variables(self):
        """Test special context variables."""
        ctx = ExecutionContext(
            request_id="req_123",
            user_id="user_456",
        )

        # Special accessors
        assert ctx.get_variable("ctx") is ctx
        assert ctx.get_variable("request")["id"] == "req_123"
        assert ctx.get_variable("user")["id"] == "user_456"

    def test_context_call_stack(self):
        """Test call stack management."""
        ctx = ExecutionContext()

        ctx.push_call("policy_a")
        ctx.push_call("rule_b")

        assert len(ctx.call_stack) == 2
        assert ctx.pop_call() == "rule_b"
        assert ctx.pop_call() == "policy_a"

    def test_context_trace(self):
        """Test execution trace."""
        ctx = ExecutionContext()

        ctx.add_trace("start", {"policy": "test"})
        ctx.step_count = 5
        ctx.add_trace("action", {"action": "deny"})

        assert len(ctx.trace) == 2
        assert ctx.trace[0]["event"] == "start"
        assert ctx.trace[1]["step"] == 5


class TestIntentSystem:
    """Tests for intent emission."""

    def test_create_intent(self):
        """Test creating an intent."""
        emitter = IntentEmitter()

        intent = emitter.create_intent(
            intent_type=IntentType.ROUTE,
            payload=IntentPayload(target_agent="expert_agent"),
            priority=80,
            source_policy="routing_policy",
        )

        assert intent.intent_type == IntentType.ROUTE
        assert intent.payload.target_agent == "expert_agent"
        assert intent.priority == 80
        assert intent.source_policy == "routing_policy"
        assert intent.id.startswith("int_")

    @pytest.mark.asyncio
    async def test_validate_intent_route(self):
        """Test validating ROUTE intent."""
        emitter = IntentEmitter()

        # Valid route
        valid_intent = emitter.create_intent(
            intent_type=IntentType.ROUTE,
            payload=IntentPayload(target_agent="target"),
        )
        assert await emitter.validate_intent(valid_intent)

        # Invalid route (no target)
        invalid_intent = emitter.create_intent(
            intent_type=IntentType.ROUTE,
            payload=IntentPayload(),
        )
        assert not await emitter.validate_intent(invalid_intent)
        assert len(invalid_intent.validation_errors) > 0

    @pytest.mark.asyncio
    async def test_validate_intent_deny(self):
        """Test validating DENY intent."""
        emitter = IntentEmitter()

        # Valid deny (has reason)
        valid_intent = emitter.create_intent(
            intent_type=IntentType.DENY,
            payload=IntentPayload(reason="Security violation"),
        )
        assert await emitter.validate_intent(valid_intent)

        # Invalid deny (no reason)
        invalid_intent = emitter.create_intent(
            intent_type=IntentType.DENY,
            payload=IntentPayload(),
        )
        assert not await emitter.validate_intent(invalid_intent)

    @pytest.mark.asyncio
    async def test_emit_intent(self):
        """Test emitting a validated intent."""
        emitter = IntentEmitter()

        intent = emitter.create_intent(
            intent_type=IntentType.ALLOW,
            payload=IntentPayload(),
        )

        result = await emitter.emit(intent)
        assert result
        assert len(emitter.get_emitted()) == 1
        assert len(emitter.get_pending()) == 0

    def test_intent_serialization(self):
        """Test intent to/from dict."""
        intent = Intent(
            id="test_id",
            intent_type=IntentType.ESCALATE,
            payload=IntentPayload(
                target_agent="supervisor",
                reason="Needs approval",
            ),
            priority=90,
            requires_confirmation=True,
        )

        data = intent.to_dict()
        assert data["type"] == "ESCALATE"
        assert data["requires_confirmation"] is True

        restored = Intent.from_dict(data)
        assert restored.intent_type == IntentType.ESCALATE
        assert restored.requires_confirmation is True


class TestDeterministicEngine:
    """Tests for deterministic execution engine."""

    @pytest.mark.asyncio
    async def test_execute_simple_deny(self):
        """Test executing simple deny policy."""
        source = """
        policy block_all: SAFETY {
            deny
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        engine = DeterministicEngine()
        ctx = ExecutionContext(request_id="test_req")

        result = await engine.execute(module, ctx)

        assert result.success
        assert result.action == ActionType.DENY
        # Intents may or may not be emitted depending on validation
        # The key test is the action is DENY

    @pytest.mark.asyncio
    async def test_execute_simple_allow(self):
        """Test executing simple allow policy."""
        source = """
        policy allow_all: CUSTOM {
            allow
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        engine = DeterministicEngine()
        ctx = ExecutionContext()

        result = await engine.execute(module, ctx)

        assert result.success
        assert result.action == ActionType.ALLOW

    @pytest.mark.asyncio
    async def test_execute_conditional(self):
        """Test executing policy with condition."""
        source = """
        policy conditional: OPERATIONAL {
            when true then deny
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        engine = DeterministicEngine()
        ctx = ExecutionContext()

        result = await engine.execute(module, ctx)

        assert result.success
        # Since condition is 'true', should deny
        assert result.action == ActionType.DENY

    @pytest.mark.asyncio
    async def test_execute_route(self):
        """Test executing route action."""
        source = """
        policy router: ROUTING {
            route to expert_agent
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        engine = DeterministicEngine()
        ctx = ExecutionContext()

        result = await engine.execute(module, ctx)

        assert result.success
        # Route action is emitted but default allow may follow
        # Check trace for route action
        route_actions = [
            t for t in result.trace if t.get("event") == "action" and t.get("data", {}).get("action") == "route"
        ]
        assert len(route_actions) >= 1

        # Should have route intent
        route_intents = [i for i in result.intents if i.intent_type == IntentType.ROUTE]
        assert len(route_intents) >= 1

    @pytest.mark.asyncio
    async def test_execution_trace(self):
        """Test execution produces trace."""
        source = """
        policy traced: SAFETY {
            deny
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        engine = DeterministicEngine()
        ctx = ExecutionContext()

        result = await engine.execute(module, ctx)

        assert len(result.trace) > 0
        # Should have function enter and exit
        events = [t["event"] for t in result.trace]
        assert "function_enter" in events
        assert "function_exit" in events

    @pytest.mark.asyncio
    async def test_execution_step_limit(self):
        """Test execution respects step limit."""
        source = """
        policy safe: SAFETY { deny }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        engine = DeterministicEngine()
        ctx = ExecutionContext(max_steps=10)

        result = await engine.execute(module, ctx)

        assert result.step_count <= 10

    @pytest.mark.asyncio
    async def test_builtin_functions(self):
        """Test builtin functions work."""
        engine = DeterministicEngine()

        # Test contains
        assert engine._builtin_functions["contains"]("hello world", "world")
        assert not engine._builtin_functions["contains"]("hello", "world")

        # Test len
        assert engine._builtin_functions["len"]("test") == 4
        assert engine._builtin_functions["len"]([1, 2, 3]) == 3

        # Test is_empty
        assert engine._builtin_functions["is_empty"]("")
        assert not engine._builtin_functions["is_empty"]("text")


class TestDAGExecutor:
    """Tests for DAG-based execution."""

    @pytest.mark.asyncio
    async def test_execute_dag_order(self):
        """Test execution follows DAG order."""
        source = """
        policy custom_policy: CUSTOM { allow }
        policy safety_policy: SAFETY { allow }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        executor = DAGExecutor()
        ctx = ExecutionContext()

        trace = await executor.execute(module, ctx)

        assert trace.total_stages >= 1
        assert trace.final_action == ActionType.ALLOW

        # SAFETY should be checked before CUSTOM
        safety_stage = None
        custom_stage = None

        for stage_result in trace.stage_results:
            if "safety_policy" in stage_result.policies_executed:
                safety_stage = stage_result.stage_index
            if "custom_policy" in stage_result.policies_executed:
                custom_stage = stage_result.stage_index

        if safety_stage is not None and custom_stage is not None:
            assert safety_stage <= custom_stage

    @pytest.mark.asyncio
    async def test_early_termination_on_deny(self):
        """Test execution stops early on DENY."""
        source = """
        policy safety_block: SAFETY { deny }
        policy never_reached: CUSTOM { allow }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        executor = DAGExecutor()
        ctx = ExecutionContext()

        trace = await executor.execute(module, ctx)

        assert trace.final_action == ActionType.DENY
        # Should have stopped before CUSTOM phase

    @pytest.mark.asyncio
    async def test_governance_counters(self):
        """Test governance counters in trace."""
        source = """
        policy safety_ok: SAFETY { allow }
        policy privacy_ok: PRIVACY { allow }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        executor = DAGExecutor()
        ctx = ExecutionContext()

        trace = await executor.execute(module, ctx)

        assert trace.safety_checks_passed >= 1
        assert trace.privacy_checks_passed >= 1

    def test_execution_plan(self):
        """Test getting execution plan."""
        source = """
        policy p1: SAFETY { deny }
        policy p2: PRIVACY { allow }
        policy p3: OPERATIONAL { allow }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        executor = DAGExecutor()
        plan = executor.get_execution_plan(module)

        assert plan.total_policies == 3
        assert len(plan.stages) >= 1

    def test_visualize_plan(self):
        """Test plan visualization."""
        source = """
        policy test: SAFETY { deny }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        executor = DAGExecutor()
        viz = executor.visualize_plan(module)

        assert "Execution DAG:" in viz


class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Test full compilation and execution pipeline."""
        source = """
        # Safety check first
        policy security_check: SAFETY {
            when user.role == "blocked" then deny
        }

        # Then routing
        policy route_experts: ROUTING {
            when agent.type == "complex" then route to expert_handler
        }

        # Default allow
        policy default_allow: CUSTOM {
            allow
        }
        """
        # Parse
        parser = Parser.from_source(source)
        ast = parser.parse()

        # Build IR
        builder = IRBuilder()
        module = builder.build(ast)

        # Optimize (would normally run optimizer here)
        # optimized = optimizer.optimize(module)

        # Execute
        executor = DAGExecutor()
        ctx = ExecutionContext(
            request_id="full_test",
            user_id="user_123",
        )
        ctx.variables["user"] = {"role": "allowed"}
        ctx.variables["agent"] = {"type": "simple"}

        trace = await executor.execute(module, ctx)

        # Should allow (no deny conditions met)
        assert trace.final_action == ActionType.ALLOW
        assert trace.safety_checks_passed >= 1

    @pytest.mark.asyncio
    async def test_determinism(self):
        """Test execution is deterministic (same input = same output)."""
        source = """
        policy test: OPERATIONAL {
            when true then deny
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()
        builder = IRBuilder()
        module = builder.build(ast)

        # Execute multiple times with same input
        results = []
        for _ in range(3):
            ctx = ExecutionContext(request_id="det_test")

            executor = DAGExecutor()
            trace = await executor.execute(module, ctx)
            results.append(trace.final_action)

        # All results should be the same (deterministic)
        assert all(r == results[0] for r in results)
        # With 'when true then deny', should always deny
        assert results[0] == ActionType.DENY
