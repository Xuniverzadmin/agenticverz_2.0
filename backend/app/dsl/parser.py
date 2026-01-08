# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Role: Policy DSL text parser (DSL → AST)
# Reference: PIN-341 Section 1.8, PIN-345

"""
Policy DSL Parser

Converts DSL text into typed, immutable AST nodes.

DESIGN CONSTRAINTS (BLOCKING - PIN-341):
- Single-pass recursive descent parser
- No external parser libraries (no PLY, no ANTLR)
- All errors must be position-aware
- Must produce valid AST or raise ParseError

GRAMMAR (Simplified EBNF):
    policy      := header clause+
    header      := 'policy' NAME 'version' INT 'scope' SCOPE 'mode' MODE
    clause      := 'when' condition 'then' action+
    condition   := or_expr
    or_expr     := and_expr ('OR' and_expr)*
    and_expr    := atom ('AND' atom)*
    atom        := predicate | exists_pred | '(' or_expr ')'
    predicate   := METRIC comparator value
    exists_pred := 'exists' '(' METRIC ')'
    comparator  := '>' | '>=' | '<' | '<=' | '==' | '!='
    value       := INT | FLOAT | STRING | BOOL
    action      := 'WARN' STRING | 'BLOCK' | 'REQUIRE_APPROVAL'

GOVERNANCE:
- Pure parsing logic
- No side effects
- No I/O, no DB
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.dsl.ast import (
    Action,
    BlockAction,
    Clause,
    Comparator,
    Condition,
    ExistsPredicate,
    LogicalCondition,
    LogicalOperator,
    Mode,
    PolicyAST,
    PolicyMetadata,
    Predicate,
    RequireApprovalAction,
    Scope,
    WarnAction,
)

# =============================================================================
# ERROR TYPES
# =============================================================================


@dataclass(frozen=True, slots=True)
class ParseLocation:
    """Source location for error reporting."""

    line: int
    column: int

    def __str__(self) -> str:
        return f"line {self.line}, column {self.column}"


class ParseError(Exception):
    """
    Raised when parsing fails.

    Contains position information for helpful error messages.
    """

    def __init__(self, message: str, location: ParseLocation | None = None) -> None:
        self.message = message
        self.location = location
        if location:
            super().__init__(f"{message} at {location}")
        else:
            super().__init__(message)


# =============================================================================
# LEXER (Tokenization)
# =============================================================================


@dataclass(frozen=True, slots=True)
class Token:
    """A lexical token with position info."""

    type: str
    value: Any
    line: int
    column: int


class Lexer:
    """
    Tokenizer for Policy DSL.

    Produces tokens from source text for the parser.
    """

    # Token patterns (order matters)
    TOKEN_PATTERNS = [
        # Keywords (must come before IDENT)
        (r"\bpolicy\b", "POLICY"),
        (r"\bversion\b", "VERSION"),
        (r"\bscope\b", "SCOPE_KW"),
        (r"\bmode\b", "MODE_KW"),
        (r"\bwhen\b", "WHEN"),
        (r"\bthen\b", "THEN"),
        (r"\bexists\b", "EXISTS"),
        (r"\bAND\b", "AND"),
        (r"\bOR\b", "OR"),
        (r"\bWARN\b", "WARN"),
        (r"\bBLOCK\b", "BLOCK"),
        (r"\bREQUIRE_APPROVAL\b", "REQUIRE_APPROVAL"),
        (r"\bORG\b", "ORG"),
        (r"\bPROJECT\b", "PROJECT"),
        (r"\bMONITOR\b", "MONITOR"),
        (r"\bENFORCE\b", "ENFORCE"),
        (r"\btrue\b", "TRUE"),
        (r"\bfalse\b", "FALSE"),
        # Comparators
        (r">=", "GTE"),
        (r"<=", "LTE"),
        (r"==", "EQ"),
        (r"!=", "NEQ"),
        (r">", "GT"),
        (r"<", "LT"),
        # Literals
        (r"-?\d+\.\d+", "FLOAT"),
        (r"-?\d+", "INT"),
        (r'"[^"]*"', "STRING"),
        (r"'[^']*'", "STRING"),
        # Identifiers (metric names)
        (r"[a-zA-Z_][a-zA-Z0-9_]*", "IDENT"),
        # Punctuation
        (r"\(", "LPAREN"),
        (r"\)", "RPAREN"),
        # Whitespace and comments (to skip)
        (r"\s+", None),  # Skip whitespace
        (r"#[^\n]*", None),  # Skip comments
    ]

    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self._compiled = [(re.compile(p), t) for p, t in self.TOKEN_PATTERNS]

    def tokenize(self) -> list[Token]:
        """Convert source text to list of tokens."""
        tokens: list[Token] = []

        while self.pos < len(self.source):
            match = None

            for pattern, token_type in self._compiled:
                match = pattern.match(self.source, self.pos)
                if match:
                    text = match.group(0)

                    if token_type is not None:  # Not whitespace/comment
                        value = self._convert_value(token_type, text)
                        tokens.append(
                            Token(
                                type=token_type,
                                value=value,
                                line=self.line,
                                column=self.column,
                            )
                        )

                    # Update position
                    self._advance(text)
                    break

            if not match:
                raise ParseError(
                    f"Unexpected character: {self.source[self.pos]!r}",
                    ParseLocation(self.line, self.column),
                )

        tokens.append(Token("EOF", None, self.line, self.column))
        return tokens

    def _advance(self, text: str) -> None:
        """Advance position, tracking line/column."""
        for char in text:
            if char == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1

    def _convert_value(self, token_type: str, text: str) -> Any:
        """Convert token text to appropriate Python value."""
        if token_type == "INT":
            return int(text)
        elif token_type == "FLOAT":
            return float(text)
        elif token_type == "STRING":
            return text[1:-1]  # Strip quotes
        elif token_type in ("TRUE", "FALSE"):
            return token_type == "TRUE"
        else:
            return text


# =============================================================================
# PARSER
# =============================================================================


class Parser:
    """
    Recursive descent parser for Policy DSL.

    Converts token stream to typed AST.
    """

    COMPARATOR_MAP = {
        "GT": Comparator.GT,
        "GTE": Comparator.GTE,
        "LT": Comparator.LT,
        "LTE": Comparator.LTE,
        "EQ": Comparator.EQ,
        "NEQ": Comparator.NEQ,
    }

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    @property
    def current(self) -> Token:
        """Current token."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF

    def error(self, message: str) -> ParseError:
        """Create a parse error at current position."""
        return ParseError(
            message,
            ParseLocation(self.current.line, self.current.column),
        )

    def expect(self, token_type: str) -> Token:
        """Consume and return token of expected type."""
        if self.current.type != token_type:
            raise self.error(f"Expected {token_type}, got {self.current.type}")
        token = self.current
        self.pos += 1
        return token

    def accept(self, *token_types: str) -> Token | None:
        """Consume token if it matches any of the types."""
        if self.current.type in token_types:
            token = self.current
            self.pos += 1
            return token
        return None

    def parse(self) -> PolicyAST:
        """Parse complete policy."""
        metadata = self._parse_header()
        clauses = self._parse_clauses()
        self.expect("EOF")
        return PolicyAST(metadata=metadata, clauses=tuple(clauses))

    def _parse_header(self) -> PolicyMetadata:
        """Parse policy header."""
        # policy <name>
        self.expect("POLICY")
        name_token = self.expect("IDENT")

        # version <n>
        self.expect("VERSION")
        version_token = self.expect("INT")

        # scope ORG|PROJECT
        self.expect("SCOPE_KW")
        scope_token = self.accept("ORG", "PROJECT")
        if not scope_token:
            raise self.error("Expected ORG or PROJECT")
        scope = Scope.ORG if scope_token.type == "ORG" else Scope.PROJECT

        # mode MONITOR|ENFORCE
        self.expect("MODE_KW")
        mode_token = self.accept("MONITOR", "ENFORCE")
        if not mode_token:
            raise self.error("Expected MONITOR or ENFORCE")
        mode = Mode.MONITOR if mode_token.type == "MONITOR" else Mode.ENFORCE

        return PolicyMetadata(
            name=name_token.value,
            version=version_token.value,
            scope=scope,
            mode=mode,
        )

    def _parse_clauses(self) -> list[Clause]:
        """Parse one or more when-then clauses."""
        clauses: list[Clause] = []

        while self.current.type == "WHEN":
            clauses.append(self._parse_clause())

        if not clauses:
            raise self.error("Policy must have at least one clause")

        return clauses

    def _parse_clause(self) -> Clause:
        """Parse a single when-then clause."""
        # when <condition>
        self.expect("WHEN")
        condition = self._parse_condition()

        # then <action>+
        self.expect("THEN")
        actions = self._parse_actions()

        return Clause(when=condition, then=tuple(actions))

    def _parse_condition(self) -> Condition:
        """Parse a condition (or_expr)."""
        return self._parse_or_expr()

    def _parse_or_expr(self) -> Condition:
        """Parse OR expression: and_expr (OR and_expr)*"""
        left = self._parse_and_expr()

        while self.accept("OR"):
            right = self._parse_and_expr()
            left = LogicalCondition(
                left=left,
                operator=LogicalOperator.OR,
                right=right,
            )

        return left

    def _parse_and_expr(self) -> Condition:
        """Parse AND expression: atom (AND atom)*"""
        left = self._parse_atom()

        while self.accept("AND"):
            right = self._parse_atom()
            left = LogicalCondition(
                left=left,
                operator=LogicalOperator.AND,
                right=right,
            )

        return left

    def _parse_atom(self) -> Condition:
        """Parse atomic condition: predicate | exists | ( or_expr )"""
        # Parenthesized expression
        if self.accept("LPAREN"):
            expr = self._parse_or_expr()
            self.expect("RPAREN")
            return expr

        # exists(metric)
        if self.accept("EXISTS"):
            self.expect("LPAREN")
            metric = self.expect("IDENT")
            self.expect("RPAREN")
            return ExistsPredicate(metric=metric.value)

        # Simple predicate: metric comparator value
        return self._parse_predicate()

    def _parse_predicate(self) -> Predicate:
        """Parse simple predicate: metric comparator value"""
        metric = self.expect("IDENT")

        # Comparator
        comp_token = self.accept("GT", "GTE", "LT", "LTE", "EQ", "NEQ")
        if not comp_token:
            raise self.error("Expected comparator (>, >=, <, <=, ==, !=)")
        comparator = self.COMPARATOR_MAP[comp_token.type]

        # Value
        value = self._parse_value()

        return Predicate(
            metric=metric.value,
            comparator=comparator,
            value=value,
        )

    def _parse_value(self) -> int | float | str | bool:
        """Parse a literal value."""
        token = self.accept("INT", "FLOAT", "STRING", "TRUE", "FALSE")
        if not token:
            raise self.error("Expected value (int, float, string, or bool)")
        return token.value

    def _parse_actions(self) -> list[Action]:
        """Parse one or more actions."""
        actions: list[Action] = []

        while True:
            action = self._try_parse_action()
            if action is None:
                break
            actions.append(action)

        if not actions:
            raise self.error("Expected at least one action (WARN, BLOCK, REQUIRE_APPROVAL)")

        return actions

    def _try_parse_action(self) -> Action | None:
        """Try to parse an action, return None if not an action."""
        if self.accept("WARN"):
            message = self.expect("STRING")
            return WarnAction(message=message.value)

        if self.accept("BLOCK"):
            return BlockAction()

        if self.accept("REQUIRE_APPROVAL"):
            return RequireApprovalAction()

        return None


# =============================================================================
# PUBLIC API
# =============================================================================


def parse(source: str) -> PolicyAST:
    """
    Parse Policy DSL text into AST.

    Args:
        source: The DSL source text

    Returns:
        PolicyAST: The parsed AST

    Raises:
        ParseError: If the source is invalid

    Example:
        >>> ast = parse('''
        ... policy CostGuard
        ... version 1
        ... scope PROJECT
        ... mode MONITOR
        ...
        ... when cost_per_hour > 200
        ... then WARN "Cost exceeded threshold"
        ... ''')
        >>> ast.name
        'CostGuard'
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def parse_condition(source: str) -> Condition:
    """
    Parse a standalone condition expression.

    Useful for testing or building conditions programmatically.

    Args:
        source: The condition expression

    Returns:
        Condition: The parsed condition

    Example:
        >>> cond = parse_condition("cost > 100 AND error_rate > 0.1")
        >>> is_logical_condition(cond)
        True
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    condition = parser._parse_condition()
    # Ensure we consumed everything except EOF
    if parser.current.type != "EOF":
        raise parser.error(f"Unexpected token after condition: {parser.current.type}")
    return condition
