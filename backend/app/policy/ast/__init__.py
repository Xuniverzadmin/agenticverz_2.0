# M20 Policy AST
# Abstract Syntax Tree for PLang v2.0
#
# AST nodes with M19 governance metadata:
# - GovernanceMetadata attached to policy/rule nodes
# - Category and priority information preserved
# - Visitor pattern for AST traversal

from app.policy.ast.nodes import (
    # Base
    ASTNode,
    ExprNode,
    # Program
    ProgramNode,
    # Declarations
    PolicyDeclNode,
    RuleDeclNode,
    ImportNode,
    RuleRefNode,
    PriorityNode,
    # Blocks
    ConditionBlockNode,
    ActionBlockNode,
    RouteTargetNode,
    # Expressions
    BinaryOpNode,
    UnaryOpNode,
    ValueNode,
    IdentNode,
    LiteralNode,
    FuncCallNode,
    AttrAccessNode,
    # Metadata
    GovernanceMetadata,
)
from app.policy.ast.visitors import (
    ASTVisitor,
    PrintVisitor,
    CategoryCollector,
    RuleExtractor,
)

__all__ = [
    # Base
    "ASTNode",
    "ExprNode",
    # Program
    "ProgramNode",
    # Declarations
    "PolicyDeclNode",
    "RuleDeclNode",
    "ImportNode",
    "RuleRefNode",
    "PriorityNode",
    # Blocks
    "ConditionBlockNode",
    "ActionBlockNode",
    "RouteTargetNode",
    # Expressions
    "BinaryOpNode",
    "UnaryOpNode",
    "ValueNode",
    "IdentNode",
    "LiteralNode",
    "FuncCallNode",
    "AttrAccessNode",
    # Metadata
    "GovernanceMetadata",
    # Visitors
    "ASTVisitor",
    "PrintVisitor",
    "CategoryCollector",
    "RuleExtractor",
]
