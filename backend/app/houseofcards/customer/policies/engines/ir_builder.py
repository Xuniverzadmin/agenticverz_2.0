# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Policy intermediate representation builder
# Callers: policy/engine
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: Policy System

# M20 Policy IR Builder
# AST to IR transformation
"""
IR Builder for PLang v2.0.

Transforms AST nodes into IR with:
- M19 category propagation
- Symbol table population
- Basic block construction
- Governance metadata attachment
"""

from typing import Any, Optional

from app.policy.ast.nodes import (
    ActionBlockNode,
    AttrAccessNode,
    BinaryOpNode,
    ConditionBlockNode,
    FuncCallNode,
    IdentNode,
    ImportNode,
    LiteralNode,
    PolicyDeclNode,
    PriorityNode,
    ProgramNode,
    RouteTargetNode,
    RuleDeclNode,
    RuleRefNode,
    UnaryOpNode,
)
from app.policy.ast.visitors import BaseVisitor
from app.policy.compiler.grammar import ActionType
from app.policy.ir.ir_nodes import (
    IRAction,
    IRBinaryOp,
    IRBlock,
    IRCall,
    IRCompare,
    IREmitIntent,
    IRFunction,
    IRGovernance,
    IRInstruction,
    IRJump,
    IRJumpIf,
    IRLoadConst,
    IRLoadVar,
    IRModule,
    IRReturn,
    IRType,
    IRUnaryOp,
)
from app.policy.ir.symbol_table import (
    Symbol,
    SymbolTable,
    SymbolType,
)


class IRBuilder(BaseVisitor):
    """
    Builds IR from PLang AST.

    Transforms AST into IR with governance metadata propagation.
    """

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.module: Optional[IRModule] = None
        self.current_function: Optional[IRFunction] = None
        self.current_block: Optional[IRBlock] = None
        self._instruction_counter = 0
        self._block_counter = 0

    def build(self, ast: ProgramNode, module_name: str = "main") -> IRModule:
        """
        Build IR module from AST.

        Args:
            ast: The program AST
            module_name: Name for the module

        Returns:
            Compiled IR module
        """
        self.module = IRModule(name=module_name)
        self._instruction_counter = 0
        self._block_counter = 0

        # First pass: collect declarations
        for stmt in ast.statements:
            if isinstance(stmt, ImportNode):
                self.module.imports.append(stmt.path)

        # Second pass: build IR
        ast.accept(self)

        return self.module

    def _next_id(self) -> int:
        """Get next instruction ID."""
        self._instruction_counter += 1
        return self._instruction_counter

    def _next_block_name(self, prefix: str = "block") -> str:
        """Get next block name."""
        self._block_counter += 1
        return f"{prefix}_{self._block_counter}"

    def _emit(self, instr: IRInstruction) -> int:
        """Emit an instruction to current block."""
        instr.id = self._next_id()
        if self.current_block:
            self.current_block.add_instruction(instr)
        return instr.id

    def _new_block(self, name: str) -> IRBlock:
        """Create a new basic block."""
        block = IRBlock(name=name)
        if self.current_function:
            self.current_function.add_block(block)
        return block

    # ========================================================================
    # Visitor Methods
    # ========================================================================

    def visit_program(self, node: ProgramNode) -> Any:
        for stmt in node.statements:
            stmt.accept(self)

    def visit_policy_decl(self, node: PolicyDeclNode) -> Any:
        # Create governance metadata
        governance = IRGovernance.from_ast(node.governance)

        # Define policy symbol
        self.symbol_table.define(
            Symbol(
                name=node.name,
                symbol_type=SymbolType.POLICY,
                category=node.category,
                priority=governance.priority,
                defined_at=node.location,
            )
        )

        # Enter policy scope
        self.symbol_table.enter_scope(node.name, node.category)

        # Create function for policy
        func = IRFunction(
            name=node.name,
            params=["ctx"],  # All policies take execution context
            return_type=IRType.ACTION,
            governance=governance,
        )
        self.current_function = func

        # Create entry block
        entry_block = self._new_block("entry")
        self.current_block = entry_block
        func.entry_block = entry_block.name

        # Process policy body
        for item in node.body:
            item.accept(self)

        # Ensure function terminates
        if not self.current_block.is_terminated:
            # Default action: allow
            self._emit(IRAction(action=ActionType.ALLOW, governance=governance))

        # Add function to module
        self.module.add_function(func)

        # Exit scope
        self.symbol_table.exit_scope()
        self.current_function = None
        self.current_block = None

    def visit_rule_decl(self, node: RuleDeclNode) -> Any:
        governance = IRGovernance.from_ast(node.governance)

        # Define rule symbol
        self.symbol_table.define(
            Symbol(
                name=node.name,
                symbol_type=SymbolType.RULE,
                category=node.category,
                priority=governance.priority,
                defined_at=node.location,
            )
        )

        # Enter rule scope
        self.symbol_table.enter_scope(node.name, node.category)

        # Create function for rule
        parent_name = self.current_function.name if self.current_function else ""
        func_name = f"{parent_name}.{node.name}" if parent_name else node.name

        func = IRFunction(
            name=func_name,
            params=["ctx"],
            return_type=IRType.ACTION,
            governance=governance,
        )

        # Save current context
        saved_function = self.current_function
        saved_block = self.current_block
        self.current_function = func

        # Create entry block
        entry_block = self._new_block("entry")
        self.current_block = entry_block
        func.entry_block = entry_block.name

        # Process rule body
        for item in node.body:
            item.accept(self)

        # Ensure function terminates
        if not self.current_block.is_terminated:
            self._emit(IRReturn())

        # Add function to module
        self.module.add_function(func)

        # Exit scope and restore context
        self.symbol_table.exit_scope()
        self.current_function = saved_function
        self.current_block = saved_block

    def visit_import(self, node: ImportNode) -> Any:
        # Imports are handled in first pass
        pass

    def visit_rule_ref(self, node: RuleRefNode) -> Any:
        # Generate call to rule function
        # Look up the rule
        symbol = self.symbol_table.lookup_rule(node.name)
        if symbol:
            func_name = f"{self.current_function.name}.{node.name}" if self.current_function else node.name
            ctx_id = self._emit(IRLoadVar(name="ctx"))
            self._emit(IRCall(callee=func_name, args=[ctx_id]))

    def visit_priority(self, node: PriorityNode) -> Any:
        # Priority is used to update governance metadata
        if self.current_function and self.current_function.governance:
            self.current_function.governance.priority = node.value

    def visit_condition_block(self, node: ConditionBlockNode) -> Any:
        # Compile condition expression
        assert node is not None
        condition_id = node.condition.accept(self)

        # Create blocks for true/false branches
        true_block = self._new_block(self._next_block_name("then"))
        false_block = self._new_block(self._next_block_name("else"))
        merge_block = self._new_block(self._next_block_name("merge"))

        # Emit conditional jump
        self._emit(
            IRJumpIf(
                condition_id=condition_id,
                true_block=true_block.name,
                false_block=false_block.name,
            )
        )

        # True branch: execute action
        self.current_block = true_block
        node.action.accept(self)
        if not self.current_block.is_terminated:
            self._emit(IRJump(target_block=merge_block.name))

        # False branch: continue
        self.current_block = false_block
        self._emit(IRJump(target_block=merge_block.name))

        # Continue from merge block
        self.current_block = merge_block

    def visit_action_block(self, node: ActionBlockNode) -> Any:
        target = node.target.target if node.target else None

        # Emit action instruction
        governance = self.current_function.governance if self.current_function else None
        self._emit(
            IRAction(
                action=node.action,
                target=target,
                governance=governance,
            )
        )

        # Emit intent for M18 execution
        if node.action in (ActionType.ROUTE, ActionType.ESCALATE):
            payload = []
            if target:
                target_id = self._emit(IRLoadConst(value=target))
                payload.append(target_id)

            self._emit(
                IREmitIntent(
                    intent_type=node.action.value,
                    payload_ids=payload,
                    priority=governance.priority if governance else 50,
                    requires_confirmation=node.action == ActionType.ESCALATE,
                )
            )

    def visit_route_target(self, node: RouteTargetNode) -> Any:
        # Handled by action_block
        pass

    # ========================================================================
    # Expression Compilation
    # ========================================================================

    def visit_binary_op(self, node: BinaryOpNode) -> int:
        assert node is not None
        left_id = node.left.accept(self)
        right_id = node.right.accept(self)

        if node.op in ("and", "or"):
            return self._emit(
                IRBinaryOp(
                    op=node.op,
                    left_id=left_id,
                    right_id=right_id,
                    result_type=IRType.BOOL,
                )
            )
        else:
            # Comparison
            return self._emit(
                IRCompare(
                    op=node.op,
                    left_id=left_id,
                    right_id=right_id,
                )
            )

    def visit_unary_op(self, node: UnaryOpNode) -> int:
        operand_id = node.operand.accept(self)
        return self._emit(
            IRUnaryOp(
                op=node.op,
                operand_id=operand_id,
                result_type=IRType.BOOL,
            )
        )

    def visit_ident(self, node: IdentNode) -> int:
        # Track reference
        self.symbol_table.add_reference(node.name, self.current_function.name if self.current_function else "global")
        return self._emit(IRLoadVar(name=node.name))

    def visit_literal(self, node: LiteralNode) -> int:
        return self._emit(IRLoadConst(value=node.value))

    def visit_func_call(self, node: FuncCallNode) -> int:
        # Compile arguments
        arg_ids = [arg.accept(self) for arg in node.args]

        # Get function name
        if isinstance(node.callee, IdentNode):
            func_name = node.callee.name
        elif isinstance(node.callee, AttrAccessNode):
            # Method call - compile object and use as first arg
            obj_id = node.callee.obj.accept(self)
            func_name = node.callee.attr
            arg_ids = [obj_id] + arg_ids
        else:
            # Should not happen in well-formed AST
            func_name = "unknown"

        return self._emit(IRCall(callee=func_name, args=arg_ids))

    def visit_attr_access(self, node: AttrAccessNode) -> int:
        obj_id = node.obj.accept(self)
        # Emit attribute load as method call with object
        return self._emit(
            IRCall(
                callee="__getattr__",
                args=[obj_id, self._emit(IRLoadConst(value=node.attr))],
            )
        )
