# M20 PLang v2.0 Parser
# Syntax analysis for policy language
"""
Parser for PLang v2.0 with M19 category support.

Produces an AST from tokens, supporting:
- Policy declarations with categories
- Rule declarations with priorities
- Condition blocks (when/then)
- Action blocks (deny/allow/escalate/route)
- Expression evaluation
"""

from typing import List, Optional

from app.policy.ast.nodes import (
    ActionBlockNode,
    ASTNode,
    AttrAccessNode,
    BinaryOpNode,
    ConditionBlockNode,
    ExprNode,
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
from app.policy.compiler.grammar import ActionType, PolicyCategory
from app.policy.compiler.tokenizer import Token, Tokenizer, TokenType


class ParseError(Exception):
    """Error during parsing."""

    def __init__(self, message: str, token: Token):
        self.message = message
        self.token = token
        super().__init__(f"Parse error at L{token.line}:{token.column}: {message}")


class Parser:
    """
    Parser for PLang v2.0.

    Converts tokens into an AST with M19 governance metadata.
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    @classmethod
    def from_source(cls, source: str) -> "Parser":
        """Create parser from source code."""
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        return cls(tokens)

    @property
    def current(self) -> Token:
        """Get current token."""
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:
        """Peek ahead by offset tokens."""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[pos]

    def advance(self) -> Token:
        """Advance to next token and return current."""
        token = self.current
        self.pos += 1
        return token

    def expect(self, token_type: TokenType) -> Token:
        """Expect current token to be of given type."""
        if self.current.type != token_type:
            raise ParseError(f"Expected {token_type.name}, got {self.current.type.name}", self.current)
        return self.advance()

    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self.current.type in token_types

    def parse(self) -> ProgramNode:
        """
        Parse the token stream into an AST.

        Returns:
            ProgramNode containing all parsed statements.
        """
        statements: List[ASTNode] = []

        while not self.match(TokenType.EOF):
            if self.match(TokenType.POLICY):
                statements.append(self.parse_policy_decl())
            elif self.match(TokenType.RULE):
                statements.append(self.parse_rule_decl())
            elif self.match(TokenType.IMPORT):
                statements.append(self.parse_import())
            else:
                raise ParseError(f"Unexpected token: {self.current.type.name}", self.current)

        return ProgramNode(statements=statements)

    def parse_policy_decl(self) -> PolicyDeclNode:
        """Parse a policy declaration."""
        start_token = self.expect(TokenType.POLICY)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.COLON)
        category = self.parse_category()
        self.expect(TokenType.LBRACE)
        body = self.parse_policy_body()
        self.expect(TokenType.RBRACE)

        return PolicyDeclNode(
            name=name,
            category=category,
            body=body,
            line=start_token.line,
            column=start_token.column,
        )

    def parse_category(self) -> PolicyCategory:
        """Parse a policy category."""
        category_tokens = {
            TokenType.SAFETY: PolicyCategory.SAFETY,
            TokenType.PRIVACY: PolicyCategory.PRIVACY,
            TokenType.OPERATIONAL: PolicyCategory.OPERATIONAL,
            TokenType.ROUTING: PolicyCategory.ROUTING,
            TokenType.CUSTOM: PolicyCategory.CUSTOM,
        }

        for token_type, category in category_tokens.items():
            if self.match(token_type):
                self.advance()
                return category

        raise ParseError("Expected policy category (SAFETY, PRIVACY, OPERATIONAL, ROUTING, CUSTOM)", self.current)

    def parse_policy_body(self) -> List[ASTNode]:
        """Parse policy body contents."""
        body: List[ASTNode] = []

        while not self.match(TokenType.RBRACE, TokenType.EOF):
            if self.match(TokenType.RULE):
                # Could be rule reference or rule declaration
                if self.peek().type == TokenType.IDENT and self.peek(2).type != TokenType.COLON:
                    body.append(self.parse_rule_ref())
                else:
                    body.append(self.parse_rule_decl())
            elif self.match(TokenType.WHEN):
                body.append(self.parse_condition_block())
            elif self.match(TokenType.DENY, TokenType.ALLOW, TokenType.ESCALATE, TokenType.ROUTE):
                body.append(self.parse_action_block())
            elif self.match(TokenType.PRIORITY):
                body.append(self.parse_priority())
            else:
                raise ParseError(f"Unexpected token in policy body: {self.current.type.name}", self.current)

        return body

    def parse_rule_decl(self) -> RuleDeclNode:
        """Parse a rule declaration."""
        start_token = self.expect(TokenType.RULE)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.COLON)
        category = self.parse_category()
        self.expect(TokenType.LBRACE)
        body = self.parse_rule_body()
        self.expect(TokenType.RBRACE)

        return RuleDeclNode(
            name=name,
            category=category,
            body=body,
            line=start_token.line,
            column=start_token.column,
        )

    def parse_rule_body(self) -> List[ASTNode]:
        """Parse rule body contents."""
        body: List[ASTNode] = []

        while not self.match(TokenType.RBRACE, TokenType.EOF):
            if self.match(TokenType.PRIORITY):
                body.append(self.parse_priority())
            elif self.match(TokenType.WHEN):
                body.append(self.parse_condition_block())
            elif self.match(TokenType.DENY, TokenType.ALLOW, TokenType.ESCALATE, TokenType.ROUTE):
                body.append(self.parse_action_block())
            else:
                raise ParseError(f"Unexpected token in rule body: {self.current.type.name}", self.current)

        return body

    def parse_rule_ref(self) -> RuleRefNode:
        """Parse a rule reference."""
        start_token = self.expect(TokenType.RULE)
        name = self.expect(TokenType.IDENT).value
        return RuleRefNode(
            name=name,
            line=start_token.line,
            column=start_token.column,
        )

    def parse_condition_block(self) -> ConditionBlockNode:
        """Parse a when/then condition block."""
        start_token = self.expect(TokenType.WHEN)
        condition = self.parse_expr()
        self.expect(TokenType.THEN)
        action = self.parse_action_block()

        return ConditionBlockNode(
            condition=condition,
            action=action,
            line=start_token.line,
            column=start_token.column,
        )

    def parse_action_block(self) -> ActionBlockNode:
        """Parse an action block."""
        start_token = self.current

        action_map = {
            TokenType.DENY: ActionType.DENY,
            TokenType.ALLOW: ActionType.ALLOW,
            TokenType.ESCALATE: ActionType.ESCALATE,
            TokenType.ROUTE: ActionType.ROUTE,
        }

        if self.current.type not in action_map:
            raise ParseError("Expected action (deny, allow, escalate, route)", self.current)

        action = action_map[self.advance().type]
        target: Optional[RouteTargetNode] = None

        if action == ActionType.ROUTE:
            target = self.parse_route_target()

        return ActionBlockNode(
            action=action,
            target=target,
            line=start_token.line,
            column=start_token.column,
        )

    def parse_route_target(self) -> RouteTargetNode:
        """Parse a route target."""
        start_token = self.expect(TokenType.TO)
        target = self.expect(TokenType.IDENT).value
        return RouteTargetNode(
            target=target,
            line=start_token.line,
            column=start_token.column,
        )

    def parse_priority(self) -> PriorityNode:
        """Parse a priority declaration."""
        start_token = self.expect(TokenType.PRIORITY)
        value = int(self.expect(TokenType.NUMBER).value)
        return PriorityNode(
            value=value,
            line=start_token.line,
            column=start_token.column,
        )

    def parse_import(self) -> ImportNode:
        """Parse an import statement."""
        start_token = self.expect(TokenType.IMPORT)
        path = self.expect(TokenType.STRING).value
        return ImportNode(
            path=path,
            line=start_token.line,
            column=start_token.column,
        )

    # Expression parsing (precedence climbing)

    def parse_expr(self) -> ExprNode:
        """Parse an expression."""
        return self.parse_or_expr()

    def parse_or_expr(self) -> ExprNode:
        """Parse OR expression."""
        left = self.parse_and_expr()

        while self.match(TokenType.OR):
            op = self.advance().value
            right = self.parse_and_expr()
            left = BinaryOpNode(
                op=op,
                left=left,
                right=right,
                line=left.line,
                column=left.column,
            )

        return left

    def parse_and_expr(self) -> ExprNode:
        """Parse AND expression."""
        left = self.parse_not_expr()

        while self.match(TokenType.AND):
            op = self.advance().value
            right = self.parse_not_expr()
            left = BinaryOpNode(
                op=op,
                left=left,
                right=right,
                line=left.line,
                column=left.column,
            )

        return left

    def parse_not_expr(self) -> ExprNode:
        """Parse NOT expression."""
        if self.match(TokenType.NOT):
            start_token = self.advance()
            operand = self.parse_not_expr()
            return UnaryOpNode(
                op="not",
                operand=operand,
                line=start_token.line,
                column=start_token.column,
            )
        return self.parse_comparison()

    def parse_comparison(self) -> ExprNode:
        """Parse comparison expression."""
        left = self.parse_value()

        comp_ops = {
            TokenType.EQ,
            TokenType.NE,
            TokenType.LT,
            TokenType.GT,
            TokenType.LE,
            TokenType.GE,
        }

        if self.current.type in comp_ops:
            op = self.advance().value
            right = self.parse_value()
            return BinaryOpNode(
                op=op,
                left=left,
                right=right,
                line=left.line,
                column=left.column,
            )

        return left

    def parse_value(self) -> ExprNode:
        """Parse a value expression."""
        start_token = self.current

        # Literals
        if self.match(TokenType.NUMBER):
            value = self.advance().value
            if "." in value:
                return LiteralNode(value=float(value), line=start_token.line, column=start_token.column)
            return LiteralNode(value=int(value), line=start_token.line, column=start_token.column)

        if self.match(TokenType.STRING):
            return LiteralNode(value=self.advance().value, line=start_token.line, column=start_token.column)

        if self.match(TokenType.TRUE):
            self.advance()
            return LiteralNode(value=True, line=start_token.line, column=start_token.column)

        if self.match(TokenType.FALSE):
            self.advance()
            return LiteralNode(value=False, line=start_token.line, column=start_token.column)

        # Identifier (could be followed by function call or attribute access)
        if self.match(TokenType.IDENT):
            name = self.advance().value
            expr: ExprNode = IdentNode(name=name, line=start_token.line, column=start_token.column)

            # Function call
            if self.match(TokenType.LPAREN):
                expr = self.parse_func_call(expr)

            # Attribute access chain
            while self.match(TokenType.DOT):
                self.advance()
                attr = self.expect(TokenType.IDENT).value
                expr = AttrAccessNode(
                    obj=expr,
                    attr=attr,
                    line=expr.line,
                    column=expr.column,
                )
                # Could be followed by function call
                if self.match(TokenType.LPAREN):
                    expr = self.parse_func_call(expr)

            return expr

        # Parenthesized expression
        if self.match(TokenType.LPAREN):
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr

        raise ParseError(f"Unexpected token in expression: {self.current.type.name}", self.current)

    def parse_func_call(self, callee: ExprNode) -> FuncCallNode:
        """Parse a function call."""
        self.expect(TokenType.LPAREN)
        args: List[ExprNode] = []

        if not self.match(TokenType.RPAREN):
            args.append(self.parse_expr())
            while self.match(TokenType.COMMA):
                self.advance()
                args.append(self.parse_expr())

        self.expect(TokenType.RPAREN)

        return FuncCallNode(
            callee=callee,
            args=args,
            line=callee.line,
            column=callee.column,
        )
