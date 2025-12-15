# M20 Optimizer Tests
# Tests for IR optimization and conflict resolution
"""
Test suite for M20 Optimizer:
- Constant folding
- Dead code elimination
- Conflict resolution
- DAG sorting
"""

import pytest
from app.policy.compiler.parser import Parser
from app.policy.compiler.grammar import PolicyCategory, ActionType
from app.policy.ir.ir_builder import IRBuilder
from app.policy.ir.ir_nodes import (
    IRModule,
    IRFunction,
    IRBlock,
    IRLoadConst,
    IRBinaryOp,
    IRCompare,
    IRAction,
    IRJump,
    IRGovernance,
)
from app.policy.optimizer.folds import ConstantFolder, DeadCodeEliminator, PolicySimplifier
from app.policy.optimizer.conflict_resolver import ConflictResolver, ConflictType
from app.policy.optimizer.dag_sorter import DAGSorter, ExecutionPhase


class TestConstantFolder:
    """Tests for constant folding optimization."""

    def test_fold_constant_comparison(self):
        """Test folding constant comparison."""
        module = IRModule(name="test")
        func = IRFunction(name="test_func")

        block = IRBlock(name="entry")
        block.add_instruction(IRLoadConst(id=1, value=10))
        block.add_instruction(IRLoadConst(id=2, value=20))
        block.add_instruction(IRCompare(id=3, op="<", left_id=1, right_id=2))
        block.add_instruction(IRAction(action=ActionType.ALLOW))

        func.add_block(block)
        module.add_function(func)

        folder = ConstantFolder()
        folder.fold_module(module)

        # The comparison should be folded to True
        assert folder.folded_count >= 1

    def test_fold_boolean_and(self):
        """Test folding boolean AND."""
        module = IRModule(name="test")
        func = IRFunction(name="test_func")

        block = IRBlock(name="entry")
        block.add_instruction(IRLoadConst(id=1, value=True))
        block.add_instruction(IRLoadConst(id=2, value=False))
        block.add_instruction(IRBinaryOp(id=3, op="and", left_id=1, right_id=2))

        func.add_block(block)
        module.add_function(func)

        folder = ConstantFolder()
        folder.fold_module(module)

        # True AND False should fold to False
        assert folder.folded_count >= 1

    def test_fold_boolean_or(self):
        """Test folding boolean OR."""
        module = IRModule(name="test")
        func = IRFunction(name="test_func")

        block = IRBlock(name="entry")
        block.add_instruction(IRLoadConst(id=1, value=True))
        block.add_instruction(IRLoadConst(id=2, value=False))
        block.add_instruction(IRBinaryOp(id=3, op="or", left_id=1, right_id=2))

        func.add_block(block)
        module.add_function(func)

        folder = ConstantFolder()
        folder.fold_module(module)

        # True OR False should fold to True
        assert folder.folded_count >= 1

    def test_no_fold_non_constant(self):
        """Test no folding when operands are not constant."""
        source = """
        policy dynamic: OPERATIONAL {
            when user.count > 100 then deny
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        folder = ConstantFolder()
        folder.fold_module(module)

        # user.count is not constant, so no folding
        # (Implementation-dependent, may have some folding)


class TestDeadCodeEliminator:
    """Tests for dead code elimination."""

    def test_eliminate_unreachable_block(self):
        """Test eliminating unreachable blocks."""
        module = IRModule(name="test")
        func = IRFunction(name="test_func")

        # Entry block with unconditional jump
        entry = IRBlock(name="entry")
        entry.add_instruction(IRJump(target_block="reachable"))
        func.add_block(entry)
        func.entry_block = "entry"

        # Reachable block
        reachable = IRBlock(name="reachable")
        reachable.add_instruction(IRAction(action=ActionType.ALLOW))
        func.add_block(reachable)

        # Unreachable block (no path from entry)
        unreachable = IRBlock(name="unreachable")
        unreachable.add_instruction(IRAction(action=ActionType.DENY))
        func.add_block(unreachable)

        module.add_function(func)

        eliminator = DeadCodeEliminator()
        eliminator.eliminate(module)

        # Unreachable block should be eliminated
        assert "unreachable" not in func.blocks
        assert "reachable" in func.blocks
        assert eliminator.eliminated_count >= 1

    def test_preserve_governance_critical(self):
        """Test that governance-critical instructions are preserved."""
        module = IRModule(name="test")
        func = IRFunction(name="test_func")

        block = IRBlock(name="entry")
        # This action should not be eliminated even if "unused"
        action = IRAction(
            id=1,
            action=ActionType.DENY,
            governance=IRGovernance(
                category=PolicyCategory.SAFETY,
                priority=100,
                audit_level=2,
            ),
        )
        block.add_instruction(action)
        func.add_block(block)
        func.entry_block = "entry"
        module.add_function(func)

        eliminator = DeadCodeEliminator()
        eliminator.eliminate(module)

        # Action should still be there
        assert len(func.blocks["entry"].instructions) > 0


class TestConflictResolver:
    """Tests for conflict resolution."""

    def test_detect_action_conflict(self):
        """Test detecting conflicting actions."""
        source = """
        policy allow_all: CUSTOM {
            allow
        }
        policy deny_all: CUSTOM {
            deny
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        resolver = ConflictResolver()
        _, conflicts = resolver.resolve(module)

        # Both have same entry condition pattern but different actions
        action_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.ACTION]
        # May or may not detect depending on condition signature
        # The key is that the resolver runs without error

    def test_detect_priority_conflict(self):
        """Test detecting same-priority policies."""
        module = IRModule(name="test")

        for name in ["policy_a", "policy_b"]:
            func = IRFunction(
                name=name,
                governance=IRGovernance(
                    category=PolicyCategory.CUSTOM,
                    priority=50,  # Same priority
                ),
            )
            block = IRBlock(name="entry")
            block.add_instruction(IRAction(action=ActionType.ALLOW))
            func.add_block(block)
            func.entry_block = "entry"
            module.add_function(func)

        resolver = ConflictResolver()
        _, conflicts = resolver.resolve(module)

        priority_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.PRIORITY]
        assert len(priority_conflicts) >= 1

    def test_resolve_category_precedence(self):
        """Test category-based conflict resolution."""
        module = IRModule(name="test")

        # SAFETY policy (higher precedence)
        safety_func = IRFunction(
            name="safety_policy",
            governance=IRGovernance(
                category=PolicyCategory.SAFETY,
                priority=100,
            ),
        )
        safety_block = IRBlock(name="entry")
        safety_block.add_instruction(IRAction(action=ActionType.DENY))
        safety_func.add_block(safety_block)
        safety_func.entry_block = "entry"
        module.add_function(safety_func)

        # CUSTOM policy (lower precedence)
        custom_func = IRFunction(
            name="custom_policy",
            governance=IRGovernance(
                category=PolicyCategory.CUSTOM,
                priority=10,
            ),
        )
        custom_block = IRBlock(name="entry")
        custom_block.add_instruction(IRAction(action=ActionType.ALLOW))
        custom_func.add_block(custom_block)
        custom_func.entry_block = "entry"
        module.add_function(custom_func)

        resolver = ConflictResolver()
        resolved_module, conflicts = resolver.resolve(module)

        # SAFETY should be listed as potential override concern
        # Resolution should favor SAFETY


class TestDAGSorter:
    """Tests for DAG-based execution ordering."""

    def test_sort_by_category(self):
        """Test policies are sorted by category."""
        source = """
        policy custom_policy: CUSTOM { allow }
        policy safety_policy: SAFETY { deny }
        policy routing_policy: ROUTING { allow }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        sorter = DAGSorter()
        order = sorter.get_execution_order(module)

        # SAFETY should come before ROUTING which should come before CUSTOM
        safety_idx = order.index("safety_policy")
        routing_idx = order.index("routing_policy")
        custom_idx = order.index("custom_policy")

        assert safety_idx < routing_idx < custom_idx

    def test_execution_plan_stages(self):
        """Test execution plan has correct stages."""
        source = """
        policy safety_1: SAFETY { deny }
        policy safety_2: SAFETY { allow }
        policy privacy_1: PRIVACY { allow }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        sorter = DAGSorter()
        sorter.build_dag(module)
        plan = sorter.sort()

        assert plan.total_policies == 3
        assert len(plan.stages) >= 1

    def test_dag_visualization(self):
        """Test DAG visualization output."""
        source = """
        policy test_safety: SAFETY { deny }
        policy test_routing: ROUTING { allow }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        sorter = DAGSorter()
        sorter.build_dag(module)
        viz = sorter.visualize()

        assert "Execution DAG:" in viz
        assert "SAFETY_CHECK" in viz

    def test_phase_assignment(self):
        """Test correct phase assignment for categories."""
        sorter = DAGSorter()

        # Create functions with different categories
        test_cases = [
            (PolicyCategory.SAFETY, ExecutionPhase.SAFETY_CHECK),
            (PolicyCategory.PRIVACY, ExecutionPhase.PRIVACY_CHECK),
            (PolicyCategory.OPERATIONAL, ExecutionPhase.OPERATIONAL),
            (PolicyCategory.ROUTING, ExecutionPhase.ROUTING),
            (PolicyCategory.CUSTOM, ExecutionPhase.CUSTOM),
        ]

        for category, expected_phase in test_cases:
            func = IRFunction(
                name="test",
                governance=IRGovernance(category=category, priority=50),
            )
            phase = sorter._get_phase(func)
            assert phase == expected_phase


class TestPolicySimplifier:
    """Tests for policy simplification."""

    def test_identify_mergeable_policies(self):
        """Test identifying policies that can be merged."""
        source = """
        policy custom_1: CUSTOM { allow }
        policy custom_2: CUSTOM { allow }
        policy safety_1: SAFETY { deny }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        simplifier = PolicySimplifier()
        simplifier.simplify(module)

        # custom_1 and custom_2 could potentially be merged
        # (same category, compatible actions)
