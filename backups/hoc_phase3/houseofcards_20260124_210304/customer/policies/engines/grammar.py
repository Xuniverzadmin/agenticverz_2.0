# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Policy language grammar definitions (pure definitions)
# Callers: policy/compiler/parser
# Allowed Imports: L6, L7
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel
# Reference: Policy System
# NOTE: Reclassified L6→L5 (2026-01-24) - no Session imports, pure definitions
#       Remains in drivers/ per Layer ≠ Directory principle

# M20 PLang v2.0 Grammar
# Policy Language Grammar with M19 Categories
"""
PLang v2.0 Grammar (EBNF):

program         ::= statement*
statement       ::= policy_decl | rule_decl | import_stmt
policy_decl     ::= 'policy' IDENT ':' category '{' policy_body '}'
category        ::= 'SAFETY' | 'PRIVACY' | 'OPERATIONAL' | 'ROUTING' | 'CUSTOM'
policy_body     ::= (rule_ref | condition_block | action_block)*
rule_ref        ::= 'rule' IDENT
condition_block ::= 'when' expr 'then' action_block
action_block    ::= 'deny' | 'allow' | 'escalate' | 'route' route_target
route_target    ::= 'to' IDENT
expr            ::= or_expr
or_expr         ::= and_expr ('or' and_expr)*
and_expr        ::= not_expr ('and' not_expr)*
not_expr        ::= 'not' not_expr | comparison
comparison      ::= value (comp_op value)?
comp_op         ::= '==' | '!=' | '<' | '>' | '<=' | '>='
value           ::= IDENT | NUMBER | STRING | 'true' | 'false' | func_call | attr_access
attr_access     ::= value '.' IDENT
func_call       ::= IDENT '(' args? ')'
args            ::= expr (',' expr)*
rule_decl       ::= 'rule' IDENT ':' category '{' rule_body '}'
rule_body       ::= (priority_decl | condition_block | action_block)*
priority_decl   ::= 'priority' NUMBER
import_stmt     ::= 'import' STRING
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Set


class GrammarNodeType(Enum):
    """Grammar node types for PLang v2.0."""

    PROGRAM = auto()
    POLICY_DECL = auto()
    RULE_DECL = auto()
    IMPORT_STMT = auto()
    CATEGORY = auto()
    POLICY_BODY = auto()
    RULE_BODY = auto()
    RULE_REF = auto()
    CONDITION_BLOCK = auto()
    ACTION_BLOCK = auto()
    ROUTE_TARGET = auto()
    PRIORITY_DECL = auto()
    # Expressions
    OR_EXPR = auto()
    AND_EXPR = auto()
    NOT_EXPR = auto()
    COMPARISON = auto()
    VALUE = auto()
    ATTR_ACCESS = auto()
    FUNC_CALL = auto()
    ARGS = auto()
    # Terminals
    IDENT = auto()
    NUMBER = auto()
    STRING = auto()
    BOOLEAN = auto()


class PolicyCategory(Enum):
    """M19 Policy Categories."""

    SAFETY = "SAFETY"
    PRIVACY = "PRIVACY"
    OPERATIONAL = "OPERATIONAL"
    ROUTING = "ROUTING"
    CUSTOM = "CUSTOM"


class ActionType(Enum):
    """Policy action types."""

    DENY = "deny"
    ALLOW = "allow"
    ESCALATE = "escalate"
    ROUTE = "route"
    LOG = "log"
    ALERT = "alert"


@dataclass
class GrammarProduction:
    """A production rule in the grammar."""

    name: str
    node_type: GrammarNodeType
    alternatives: List[List[str]]  # Each alternative is a list of symbols
    is_terminal: bool = False


@dataclass
class PLangGrammar:
    """PLang v2.0 Grammar Definition."""

    # Keywords
    KEYWORDS: Set[str] = field(
        default_factory=lambda: {
            "policy",
            "rule",
            "when",
            "then",
            "import",
            "deny",
            "allow",
            "escalate",
            "route",
            "to",
            "and",
            "or",
            "not",
            "true",
            "false",
            "priority",
            "SAFETY",
            "PRIVACY",
            "OPERATIONAL",
            "ROUTING",
            "CUSTOM",
        }
    )

    # Operators
    OPERATORS: Set[str] = field(
        default_factory=lambda: {
            "==",
            "!=",
            "<",
            ">",
            "<=",
            ">=",
            "(",
            ")",
            "{",
            "}",
            ":",
            ",",
            ".",
        }
    )

    # Category mapping for governance
    CATEGORY_PRIORITY: Dict[str, int] = field(
        default_factory=lambda: {
            "SAFETY": 100,  # Highest priority - safety first
            "PRIVACY": 90,  # High priority - data protection
            "OPERATIONAL": 50,  # Medium priority - business rules
            "ROUTING": 30,  # Lower priority - routing decisions
            "CUSTOM": 10,  # Lowest priority - custom policies
        }
    )

    # Action precedence (higher = more restrictive)
    ACTION_PRECEDENCE: Dict[str, int] = field(
        default_factory=lambda: {
            "deny": 100,  # Most restrictive
            "escalate": 80,
            "route": 50,
            "allow": 10,  # Least restrictive
            "log": 5,
            "alert": 5,
        }
    )

    def get_category_priority(self, category: str) -> int:
        """Get priority for a policy category."""
        return self.CATEGORY_PRIORITY.get(category, 0)

    def get_action_precedence(self, action: str) -> int:
        """Get precedence for an action type."""
        return self.ACTION_PRECEDENCE.get(action, 0)

    def is_keyword(self, word: str) -> bool:
        """Check if word is a PLang keyword."""
        return word in self.KEYWORDS

    def is_operator(self, char: str) -> bool:
        """Check if character is part of an operator."""
        return char in "=!<>(){}:,."

    def is_category(self, word: str) -> bool:
        """Check if word is a valid M19 category."""
        return word in {"SAFETY", "PRIVACY", "OPERATIONAL", "ROUTING", "CUSTOM"}

    def is_action(self, word: str) -> bool:
        """Check if word is a valid action."""
        return word in {"deny", "allow", "escalate", "route", "log", "alert"}


# Global grammar instance
PLANG_GRAMMAR = PLangGrammar()
