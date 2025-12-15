# M20 Parser Tests
# Tests for PLang v2.0 tokenizer and parser
"""
Test suite for M20 Policy Compiler:
- Tokenization
- Parsing
- AST generation
- Category handling
"""

import pytest
from app.policy.compiler.tokenizer import Tokenizer, Token, TokenType, TokenizerError
from app.policy.compiler.parser import Parser, ParseError
from app.policy.compiler.grammar import PolicyCategory, ActionType
from app.policy.ast.nodes import (
    ProgramNode,
    PolicyDeclNode,
    RuleDeclNode,
    ConditionBlockNode,
    ActionBlockNode,
    BinaryOpNode,
    LiteralNode,
    IdentNode,
)


class TestTokenizer:
    """Tests for PLang tokenizer."""

    def test_tokenize_simple_policy(self):
        """Test tokenizing a simple policy declaration."""
        source = 'policy test_policy: SAFETY { deny }'
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()

        assert len(tokens) > 0
        assert tokens[0].type == TokenType.POLICY
        assert tokens[1].type == TokenType.IDENT
        assert tokens[1].value == "test_policy"
        assert tokens[2].type == TokenType.COLON
        assert tokens[3].type == TokenType.SAFETY

    def test_tokenize_keywords(self):
        """Test all keywords are tokenized correctly."""
        keywords = [
            ("policy", TokenType.POLICY),
            ("rule", TokenType.RULE),
            ("when", TokenType.WHEN),
            ("then", TokenType.THEN),
            ("deny", TokenType.DENY),
            ("allow", TokenType.ALLOW),
            ("escalate", TokenType.ESCALATE),
            ("route", TokenType.ROUTE),
            ("and", TokenType.AND),
            ("or", TokenType.OR),
            ("not", TokenType.NOT),
            ("true", TokenType.TRUE),
            ("false", TokenType.FALSE),
        ]

        for keyword, expected_type in keywords:
            tokenizer = Tokenizer(keyword)
            tokens = tokenizer.tokenize()
            assert tokens[0].type == expected_type, f"Failed for keyword: {keyword}"

    def test_tokenize_categories(self):
        """Test M19 categories are tokenized correctly."""
        categories = [
            ("SAFETY", TokenType.SAFETY),
            ("PRIVACY", TokenType.PRIVACY),
            ("OPERATIONAL", TokenType.OPERATIONAL),
            ("ROUTING", TokenType.ROUTING),
            ("CUSTOM", TokenType.CUSTOM),
        ]

        for category, expected_type in categories:
            tokenizer = Tokenizer(category)
            tokens = tokenizer.tokenize()
            assert tokens[0].type == expected_type

    def test_tokenize_operators(self):
        """Test operators are tokenized correctly."""
        operators = [
            ("==", TokenType.EQ),
            ("!=", TokenType.NE),
            ("<", TokenType.LT),
            (">", TokenType.GT),
            ("<=", TokenType.LE),
            (">=", TokenType.GE),
        ]

        for op, expected_type in operators:
            tokenizer = Tokenizer(op)
            tokens = tokenizer.tokenize()
            assert tokens[0].type == expected_type, f"Failed for operator: {op}"

    def test_tokenize_string_literal(self):
        """Test string literals are tokenized correctly."""
        tokenizer = Tokenizer('"hello world"')
        tokens = tokenizer.tokenize()

        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello world"

    def test_tokenize_number_literal(self):
        """Test number literals are tokenized correctly."""
        tokenizer = Tokenizer("42 3.14")
        tokens = tokenizer.tokenize()

        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"
        assert tokens[1].type == TokenType.NUMBER
        assert tokens[1].value == "3.14"

    def test_tokenize_comments(self):
        """Test comments are skipped."""
        source = """
        # This is a comment
        policy test: SAFETY {
            # Another comment
            deny
        }
        """
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()

        # Comments should not appear in tokens
        comment_tokens = [t for t in tokens if t.type == TokenType.COMMENT]
        assert len(comment_tokens) == 0

    def test_tokenize_error_unterminated_string(self):
        """Test error on unterminated string."""
        tokenizer = Tokenizer('"unterminated')
        with pytest.raises(TokenizerError):
            tokenizer.tokenize()

    def test_token_location(self):
        """Test token location tracking."""
        source = "policy test"
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()

        assert tokens[0].line == 1
        assert tokens[0].column == 1
        assert tokens[1].line == 1
        assert tokens[1].column == 8


class TestParser:
    """Tests for PLang parser."""

    def test_parse_simple_policy(self):
        """Test parsing a simple policy."""
        source = """
        policy no_secrets: SAFETY {
            deny
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        assert isinstance(ast, ProgramNode)
        assert len(ast.statements) == 1
        assert isinstance(ast.statements[0], PolicyDeclNode)

        policy = ast.statements[0]
        assert policy.name == "no_secrets"
        assert policy.category == PolicyCategory.SAFETY

    def test_parse_policy_with_condition(self):
        """Test parsing policy with when/then condition."""
        source = """
        policy rate_limit: OPERATIONAL {
            when user.requests > 100 then deny
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        policy = ast.statements[0]
        assert len(policy.body) == 1
        assert isinstance(policy.body[0], ConditionBlockNode)

        condition_block = policy.body[0]
        assert isinstance(condition_block.condition, BinaryOpNode)
        assert isinstance(condition_block.action, ActionBlockNode)
        assert condition_block.action.action == ActionType.DENY

    def test_parse_policy_with_route(self):
        """Test parsing policy with route action."""
        source = """
        policy route_complex: ROUTING {
            when agent.type == "specialist" then route to expert_agent
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        policy = ast.statements[0]
        condition_block = policy.body[0]

        assert condition_block.action.action == ActionType.ROUTE
        assert condition_block.action.target.target == "expert_agent"

    def test_parse_nested_conditions(self):
        """Test parsing nested boolean conditions."""
        source = """
        policy complex_check: SAFETY {
            when user.role == "admin" and not user.suspended then allow
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        policy = ast.statements[0]
        condition_block = policy.body[0]

        # Should be: (user.role == "admin") AND (NOT user.suspended)
        assert isinstance(condition_block.condition, BinaryOpNode)
        assert condition_block.condition.op == "and"

    def test_parse_rule_declaration(self):
        """Test parsing rule declaration."""
        source = """
        rule budget_check: OPERATIONAL {
            priority 80
            when budget.remaining < 10 then escalate
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        rule = ast.statements[0]
        assert isinstance(rule, RuleDeclNode)
        assert rule.name == "budget_check"
        assert rule.category == PolicyCategory.OPERATIONAL

    def test_parse_import(self):
        """Test parsing import statement."""
        source = 'import "base_policies.plang"'
        parser = Parser.from_source(source)
        ast = parser.parse()

        assert len(ast.statements) == 1
        import_node = ast.statements[0]
        assert import_node.path == "base_policies.plang"

    def test_parse_function_call(self):
        """Test parsing function call in condition."""
        source = """
        policy check_content: SAFETY {
            when contains(user.input, "secret") then deny
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        policy = ast.statements[0]
        condition_block = policy.body[0]

        # The condition should be a function call
        from app.policy.ast.nodes import FuncCallNode
        assert isinstance(condition_block.condition, FuncCallNode)

    def test_parse_all_categories(self):
        """Test parsing all M19 categories."""
        categories = ["SAFETY", "PRIVACY", "OPERATIONAL", "ROUTING", "CUSTOM"]

        for category in categories:
            source = f"policy test_{category.lower()}: {category} {{ allow }}"
            parser = Parser.from_source(source)
            ast = parser.parse()

            policy = ast.statements[0]
            assert policy.category == PolicyCategory[category]

    def test_parse_error_missing_category(self):
        """Test parse error on missing category."""
        source = "policy test: { deny }"
        parser = Parser.from_source(source)

        with pytest.raises(ParseError):
            parser.parse()

    def test_parse_error_missing_brace(self):
        """Test parse error on missing brace."""
        source = "policy test: SAFETY { deny"  # Missing closing brace
        parser = Parser.from_source(source)

        with pytest.raises(ParseError):
            parser.parse()


class TestASTVisitors:
    """Tests for AST visitors."""

    def test_print_visitor(self):
        """Test PrintVisitor generates readable output."""
        from app.policy.ast.visitors import PrintVisitor

        source = """
        policy test_policy: SAFETY {
            when user.role == "admin" then allow
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        visitor = PrintVisitor()
        output = ast.accept(visitor)

        assert "Program:" in output
        assert "Policy 'test_policy'" in output
        assert "SAFETY" in output

    def test_category_collector(self):
        """Test CategoryCollector finds all categories."""
        from app.policy.ast.visitors import CategoryCollector

        source = """
        policy safety_policy: SAFETY { deny }
        policy privacy_policy: PRIVACY { deny }
        policy routing_policy: ROUTING { allow }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        visitor = CategoryCollector()
        ast.accept(visitor)
        categories = visitor.get_categories()

        assert "safety_policy" in categories[PolicyCategory.SAFETY]
        assert "privacy_policy" in categories[PolicyCategory.PRIVACY]
        assert "routing_policy" in categories[PolicyCategory.ROUTING]

    def test_rule_extractor(self):
        """Test RuleExtractor extracts rules with metadata."""
        from app.policy.ast.visitors import RuleExtractor

        source = """
        policy main_policy: SAFETY {
            rule check_input: SAFETY {
                priority 90
                when input.length > 1000 then deny
            }
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        visitor = RuleExtractor()
        ast.accept(visitor)
        rules = visitor.get_rules()

        assert "main_policy" in rules
        assert rules["main_policy"]["type"] == "policy"
        assert rules["main_policy"]["category"] == PolicyCategory.SAFETY


class TestGovernanceMetadata:
    """Tests for governance metadata in AST."""

    def test_policy_has_governance(self):
        """Test policy declaration has governance metadata."""
        source = "policy test: SAFETY { deny }"
        parser = Parser.from_source(source)
        ast = parser.parse()

        policy = ast.statements[0]
        assert policy.governance is not None
        assert policy.governance.category == PolicyCategory.SAFETY
        assert policy.governance.priority == 100  # SAFETY priority

    def test_rule_has_governance(self):
        """Test rule declaration has governance metadata."""
        source = "rule test_rule: PRIVACY { allow }"
        parser = Parser.from_source(source)
        ast = parser.parse()

        rule = ast.statements[0]
        assert rule.governance is not None
        assert rule.governance.category == PolicyCategory.PRIVACY
        assert rule.governance.priority == 90  # PRIVACY priority

    def test_governance_source_tracking(self):
        """Test governance tracks source policy/rule."""
        source = """
        policy parent_policy: OPERATIONAL {
            when true then allow
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        policy = ast.statements[0]
        assert policy.governance.source_policy == "parent_policy"
