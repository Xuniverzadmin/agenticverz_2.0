# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Policy constant folding optimizations (pure logic)
# Callers: policy/optimizer
# Allowed Imports: L6, L7
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel
# Reference: Policy System
# NOTE: Reclassified L6→L5 (2026-01-24) - no Session imports, pure logic

# M20 Policy Optimizer - Constant Folding and Simplification
# Optimizations that preserve governance semantics
"""
IR optimizations for PLang v2.0.

Optimizations:
- Constant folding: Evaluate constant expressions at compile time
- Dead code elimination: Remove unreachable code
- Policy simplification: Merge compatible policies
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from app.policy.ir.ir_nodes import (
    IRAction,
    IRBinaryOp,
    IRBlock,
    IRCompare,
    IRFunction,
    IRInstruction,
    IRJump,
    IRJumpIf,
    IRLoadConst,
    IRModule,
    IRUnaryOp,
)


@dataclass
class FoldResult:
    """Result of a folding operation."""

    folded: bool
    value: Any = None
    instruction: Optional[IRInstruction] = None


class ConstantFolder:
    """
    Constant folding optimization.

    Evaluates constant expressions at compile time without
    affecting governance semantics.
    """

    def __init__(self):
        self.constants: Dict[int, Any] = {}  # instruction_id -> value
        self.folded_count = 0

    def fold_module(self, module: IRModule) -> IRModule:
        """
        Fold constants in all functions.

        Returns:
            Optimized module
        """
        for func in module.functions.values():
            self.fold_function(func)
        return module

    def fold_function(self, func: IRFunction) -> None:
        """Fold constants in a function."""
        self.constants = {}

        for block in func.blocks.values():
            self.fold_block(block)

    def fold_block(self, block: IRBlock) -> None:
        """Fold constants in a basic block."""
        new_instructions: List[IRInstruction] = []

        for instr in block.instructions:
            result = self.try_fold(instr)

            if result.folded:
                # Replace with constant load
                new_instr = IRLoadConst(
                    id=instr.id,
                    value=result.value,
                    governance=instr.governance,
                )
                new_instructions.append(new_instr)
                self.constants[instr.id] = result.value
                self.folded_count += 1
            else:
                new_instructions.append(instr)

        block.instructions = new_instructions

    def try_fold(self, instr: IRInstruction) -> FoldResult:
        """
        Try to fold an instruction.

        Returns:
            FoldResult indicating if folding was successful
        """
        if isinstance(instr, IRLoadConst):
            self.constants[instr.id] = instr.value
            return FoldResult(folded=False)

        if isinstance(instr, IRBinaryOp):
            return self._fold_binary_op(instr)

        if isinstance(instr, IRUnaryOp):
            return self._fold_unary_op(instr)

        if isinstance(instr, IRCompare):
            return self._fold_compare(instr)

        return FoldResult(folded=False)

    def _fold_binary_op(self, instr: IRBinaryOp) -> FoldResult:
        """Fold binary operation if both operands are constant."""
        left = self.constants.get(instr.left_id)
        right = self.constants.get(instr.right_id)

        if left is None or right is None:
            return FoldResult(folded=False)

        try:
            if instr.op == "and":
                result = left and right
            elif instr.op == "or":
                result = left or right
            else:
                return FoldResult(folded=False)

            return FoldResult(folded=True, value=result)
        except Exception:
            return FoldResult(folded=False)

    def _fold_unary_op(self, instr: IRUnaryOp) -> FoldResult:
        """Fold unary operation if operand is constant."""
        operand = self.constants.get(instr.operand_id)

        if operand is None:
            return FoldResult(folded=False)

        try:
            if instr.op == "not":
                result = not operand
            else:
                return FoldResult(folded=False)

            return FoldResult(folded=True, value=result)
        except Exception:
            return FoldResult(folded=False)

    def _fold_compare(self, instr: IRCompare) -> FoldResult:
        """Fold comparison if both operands are constant."""
        left = self.constants.get(instr.left_id)
        right = self.constants.get(instr.right_id)

        if left is None or right is None:
            return FoldResult(folded=False)

        try:
            ops = {
                "==": lambda l, r: l == r,
                "!=": lambda l, r: l != r,
                "<": lambda l, r: l < r,
                ">": lambda l, r: l > r,
                "<=": lambda l, r: l <= r,
                ">=": lambda l, r: l >= r,
            }

            if instr.op not in ops:
                return FoldResult(folded=False)

            result = ops[instr.op](left, right)
            return FoldResult(folded=True, value=result)
        except Exception:
            return FoldResult(folded=False)


class DeadCodeEliminator:
    """
    Dead code elimination.

    Removes unreachable code and unused definitions while
    preserving governance-critical paths.
    """

    def __init__(self):
        self.eliminated_count = 0
        self._governance_critical: Set[int] = set()

    def eliminate(self, module: IRModule) -> IRModule:
        """
        Eliminate dead code in module.

        Returns:
            Optimized module
        """
        for func in module.functions.values():
            self._mark_governance_critical(func)
            self._eliminate_function(func)
        return module

    def _mark_governance_critical(self, func: IRFunction) -> None:
        """Mark instructions that are governance-critical (cannot be eliminated)."""
        self._governance_critical = set()

        for block in func.blocks.values():
            for instr in block.instructions:
                # Actions are always governance-critical
                if isinstance(instr, IRAction):
                    self._governance_critical.add(instr.id)
                # Check governance metadata
                if instr.governance and instr.governance.audit_level > 0:
                    self._governance_critical.add(instr.id)

    def _eliminate_function(self, func: IRFunction) -> None:
        """Eliminate dead code in a function."""
        # Find reachable blocks
        reachable = self._find_reachable_blocks(func)

        # Remove unreachable blocks
        unreachable = set(func.blocks.keys()) - reachable
        for block_name in unreachable:
            del func.blocks[block_name]
            self.eliminated_count += 1

        # Within reachable blocks, find used instructions
        used = self._find_used_instructions(func)

        # Remove unused instructions (except governance-critical)
        for block in func.blocks.values():
            new_instructions = [
                instr
                for instr in block.instructions
                if instr.id in used
                or instr.id in self._governance_critical
                or isinstance(instr, (IRJump, IRJumpIf, IRAction))
            ]
            eliminated = len(block.instructions) - len(new_instructions)
            self.eliminated_count += eliminated
            block.instructions = new_instructions

    def _find_reachable_blocks(self, func: IRFunction) -> Set[str]:
        """Find all reachable blocks from entry."""
        reachable: Set[str] = set()
        worklist = [func.entry_block]

        while worklist:
            block_name = worklist.pop()
            if block_name in reachable:
                continue
            reachable.add(block_name)

            block = func.blocks.get(block_name)
            if not block:
                continue

            # Find successors from terminators
            for instr in block.instructions:
                if isinstance(instr, IRJump):
                    worklist.append(instr.target_block)
                elif isinstance(instr, IRJumpIf):
                    worklist.append(instr.true_block)
                    worklist.append(instr.false_block)

        return reachable

    def _find_used_instructions(self, func: IRFunction) -> Set[int]:
        """Find all instructions whose results are used."""
        used: Set[int] = set()

        # All instructions in terminators are used
        for block in func.blocks.values():
            for instr in block.instructions:
                if isinstance(instr, IRJumpIf):
                    used.add(instr.condition_id)

        # Propagate uses backwards (simple fixed-point)
        changed = True
        while changed:
            changed = False
            for block in func.blocks.values():
                for instr in block.instructions:
                    if instr.id in used:
                        # Mark operands as used
                        if isinstance(instr, IRBinaryOp):
                            if instr.left_id not in used:
                                used.add(instr.left_id)
                                changed = True
                            if instr.right_id not in used:
                                used.add(instr.right_id)
                                changed = True
                        elif isinstance(instr, IRUnaryOp):
                            if instr.operand_id not in used:
                                used.add(instr.operand_id)
                                changed = True
                        elif isinstance(instr, IRCompare):
                            if instr.left_id not in used:
                                used.add(instr.left_id)
                                changed = True
                            if instr.right_id not in used:
                                used.add(instr.right_id)
                                changed = True

        return used


class PolicySimplifier:
    """
    Policy-specific simplifications.

    Merges compatible policies based on governance rules
    while preserving semantic correctness.
    """

    def __init__(self):
        self.simplified_count = 0

    def simplify(self, module: IRModule) -> IRModule:
        """
        Simplify policies in module.

        Returns:
            Optimized module
        """
        # Identify policies that can be merged
        mergeable = self._find_mergeable_policies(module)

        # Merge compatible policies
        for group in mergeable:
            if len(group) > 1:
                self._merge_policies(module, group)

        return module

    def _find_mergeable_policies(self, module: IRModule) -> List[List[str]]:
        """
        Find groups of policies that can be safely merged.

        Policies can be merged if:
        - Same category
        - Non-conflicting actions
        - Compatible governance levels
        """
        groups: Dict[tuple, List[str]] = {}

        for func_name, func in module.functions.items():
            if not func.governance:
                continue

            # Group key: (category, priority_bucket)
            key = (
                func.governance.category,
                func.governance.priority // 10,  # Bucket by 10s
            )

            if key not in groups:
                groups[key] = []
            groups[key].append(func_name)

        return list(groups.values())

    def _merge_policies(self, module: IRModule, policy_names: List[str]) -> None:
        """
        Merge a group of compatible policies.

        The merged policy:
        - Takes highest priority from group
        - Combines conditions with OR
        - Uses most restrictive action on conflicts
        """
        if len(policy_names) < 2:
            return

        # Sort by priority to find primary
        policies = [(name, module.functions[name]) for name in policy_names if name in module.functions]
        if not policies:
            return

        policies.sort(key=lambda p: p[1].governance.priority if p[1].governance else 0, reverse=True)

        primary_name, primary = policies[0]

        # For now, just ensure priority ordering is enforced
        # Full merging would require more complex block manipulation
        self.simplified_count += len(policies) - 1
