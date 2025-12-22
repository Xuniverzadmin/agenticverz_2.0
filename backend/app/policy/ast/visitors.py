# M20 Policy AST Visitors
# Visitor pattern implementations for AST traversal
"""
AST visitors for PLang v2.0.

Visitors for:
- Pretty printing
- Category collection
- Rule extraction
- Governance analysis
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

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
from app.policy.compiler.grammar import PolicyCategory


class ASTVisitor(ABC):
    """
    Base visitor interface for AST traversal.

    Implements the visitor pattern for PLang AST.
    """

    @abstractmethod
    def visit_program(self, node: ProgramNode) -> Any:
        pass

    @abstractmethod
    def visit_policy_decl(self, node: PolicyDeclNode) -> Any:
        pass

    @abstractmethod
    def visit_rule_decl(self, node: RuleDeclNode) -> Any:
        pass

    @abstractmethod
    def visit_import(self, node: ImportNode) -> Any:
        pass

    @abstractmethod
    def visit_rule_ref(self, node: RuleRefNode) -> Any:
        pass

    @abstractmethod
    def visit_priority(self, node: PriorityNode) -> Any:
        pass

    @abstractmethod
    def visit_condition_block(self, node: ConditionBlockNode) -> Any:
        pass

    @abstractmethod
    def visit_action_block(self, node: ActionBlockNode) -> Any:
        pass

    @abstractmethod
    def visit_route_target(self, node: RouteTargetNode) -> Any:
        pass

    @abstractmethod
    def visit_binary_op(self, node: BinaryOpNode) -> Any:
        pass

    @abstractmethod
    def visit_unary_op(self, node: UnaryOpNode) -> Any:
        pass

    @abstractmethod
    def visit_ident(self, node: IdentNode) -> Any:
        pass

    @abstractmethod
    def visit_literal(self, node: LiteralNode) -> Any:
        pass

    @abstractmethod
    def visit_func_call(self, node: FuncCallNode) -> Any:
        pass

    @abstractmethod
    def visit_attr_access(self, node: AttrAccessNode) -> Any:
        pass


class BaseVisitor(ASTVisitor):
    """Base visitor with default implementations."""

    def visit_program(self, node: ProgramNode) -> Any:
        for stmt in node.statements:
            stmt.accept(self)

    def visit_policy_decl(self, node: PolicyDeclNode) -> Any:
        for item in node.body:
            item.accept(self)

    def visit_rule_decl(self, node: RuleDeclNode) -> Any:
        for item in node.body:
            item.accept(self)

    def visit_import(self, node: ImportNode) -> Any:
        pass

    def visit_rule_ref(self, node: RuleRefNode) -> Any:
        pass

    def visit_priority(self, node: PriorityNode) -> Any:
        pass

    def visit_condition_block(self, node: ConditionBlockNode) -> Any:
        if node.condition:
            node.condition.accept(self)
        if node.action:
            node.action.accept(self)

    def visit_action_block(self, node: ActionBlockNode) -> Any:
        if node.target:
            node.target.accept(self)

    def visit_route_target(self, node: RouteTargetNode) -> Any:
        pass

    def visit_binary_op(self, node: BinaryOpNode) -> Any:
        if node.left:
            node.left.accept(self)
        if node.right:
            node.right.accept(self)

    def visit_unary_op(self, node: UnaryOpNode) -> Any:
        if node.operand:
            node.operand.accept(self)

    def visit_ident(self, node: IdentNode) -> Any:
        pass

    def visit_literal(self, node: LiteralNode) -> Any:
        pass

    def visit_func_call(self, node: FuncCallNode) -> Any:
        if node.callee:
            node.callee.accept(self)
        for arg in node.args:
            arg.accept(self)

    def visit_attr_access(self, node: AttrAccessNode) -> Any:
        if node.obj:
            node.obj.accept(self)


class PrintVisitor(BaseVisitor):
    """Visitor that prints AST in readable format."""

    def __init__(self):
        self.indent = 0
        self.output: List[str] = []

    def _emit(self, text: str) -> None:
        self.output.append("  " * self.indent + text)

    def get_output(self) -> str:
        return "\n".join(self.output)

    def visit_program(self, node: ProgramNode) -> str:
        self._emit("Program:")
        self.indent += 1
        for stmt in node.statements:
            stmt.accept(self)
        self.indent -= 1
        return self.get_output()

    def visit_policy_decl(self, node: PolicyDeclNode) -> Any:
        self._emit(f"Policy '{node.name}' [{node.category.value}]:")
        self.indent += 1
        for item in node.body:
            item.accept(self)
        self.indent -= 1

    def visit_rule_decl(self, node: RuleDeclNode) -> Any:
        self._emit(f"Rule '{node.name}' [{node.category.value}]:")
        self.indent += 1
        for item in node.body:
            item.accept(self)
        self.indent -= 1

    def visit_import(self, node: ImportNode) -> Any:
        self._emit(f"Import: {node.path}")

    def visit_rule_ref(self, node: RuleRefNode) -> Any:
        self._emit(f"RuleRef: {node.name}")

    def visit_priority(self, node: PriorityNode) -> Any:
        self._emit(f"Priority: {node.value}")

    def visit_condition_block(self, node: ConditionBlockNode) -> Any:
        self._emit("When:")
        self.indent += 1
        node.condition.accept(self)
        self.indent -= 1
        self._emit("Then:")
        self.indent += 1
        node.action.accept(self)
        self.indent -= 1

    def visit_action_block(self, node: ActionBlockNode) -> Any:
        target_str = f" to {node.target.target}" if node.target else ""
        self._emit(f"Action: {node.action.value}{target_str}")

    def visit_route_target(self, node: RouteTargetNode) -> Any:
        self._emit(f"Target: {node.target}")

    def visit_binary_op(self, node: BinaryOpNode) -> Any:
        self._emit(f"BinaryOp: {node.op}")
        self.indent += 1
        node.left.accept(self)
        node.right.accept(self)
        self.indent -= 1

    def visit_unary_op(self, node: UnaryOpNode) -> Any:
        self._emit(f"UnaryOp: {node.op}")
        self.indent += 1
        node.operand.accept(self)
        self.indent -= 1

    def visit_ident(self, node: IdentNode) -> Any:
        self._emit(f"Ident: {node.name}")

    def visit_literal(self, node: LiteralNode) -> Any:
        self._emit(f"Literal: {node.value!r}")

    def visit_func_call(self, node: FuncCallNode) -> Any:
        self._emit("FuncCall:")
        self.indent += 1
        node.callee.accept(self)
        self._emit("Args:")
        self.indent += 1
        for arg in node.args:
            arg.accept(self)
        self.indent -= 2

    def visit_attr_access(self, node: AttrAccessNode) -> Any:
        self._emit(f"AttrAccess: .{node.attr}")
        self.indent += 1
        node.obj.accept(self)
        self.indent -= 1


class CategoryCollector(BaseVisitor):
    """
    Visitor that collects all categories used in the AST.

    Used for governance analysis and category-based routing.
    """

    def __init__(self):
        self.categories: Dict[PolicyCategory, List[str]] = {cat: [] for cat in PolicyCategory}
        self._current_policy: str = ""

    def get_categories(self) -> Dict[PolicyCategory, List[str]]:
        return self.categories

    def visit_policy_decl(self, node: PolicyDeclNode) -> Any:
        self._current_policy = node.name
        self.categories[node.category].append(node.name)
        super().visit_policy_decl(node)

    def visit_rule_decl(self, node: RuleDeclNode) -> Any:
        if node.category not in self.categories:
            self.categories[node.category] = []
        self.categories[node.category].append(
            f"{self._current_policy}.{node.name}" if self._current_policy else node.name
        )
        super().visit_rule_decl(node)


class RuleExtractor(BaseVisitor):
    """
    Visitor that extracts all rules with their governance metadata.

    Used for building the symbol table and IR.
    """

    def __init__(self):
        self.rules: Dict[str, Dict[str, Any]] = {}
        self._current_policy: str = ""
        self._current_category: PolicyCategory = PolicyCategory.CUSTOM

    def get_rules(self) -> Dict[str, Dict[str, Any]]:
        return self.rules

    def visit_policy_decl(self, node: PolicyDeclNode) -> Any:
        self._current_policy = node.name
        self._current_category = node.category

        # Store policy metadata
        self.rules[node.name] = {
            "type": "policy",
            "category": node.category,
            "priority": node.governance.priority if node.governance else 50,
            "rules": [],
            "conditions": [],
        }

        super().visit_policy_decl(node)

    def visit_rule_decl(self, node: RuleDeclNode) -> Any:
        rule_name = f"{self._current_policy}.{node.name}" if self._current_policy else node.name

        self.rules[rule_name] = {
            "type": "rule",
            "category": node.category,
            "priority": node.governance.priority if node.governance else 50,
            "parent_policy": self._current_policy,
            "conditions": [],
        }

        # Add to parent policy's rules
        if self._current_policy in self.rules:
            self.rules[self._current_policy]["rules"].append(rule_name)

        super().visit_rule_decl(node)

    def visit_condition_block(self, node: ConditionBlockNode) -> Any:
        # Track conditions for current rule/policy
        condition_info = {
            "action": node.action.action.value if node.action else None,
            "target": node.action.target.target if node.action and node.action.target else None,
        }

        if self._current_policy in self.rules:
            self.rules[self._current_policy]["conditions"].append(condition_info)

        super().visit_condition_block(node)
