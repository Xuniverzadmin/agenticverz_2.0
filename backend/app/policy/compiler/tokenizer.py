# M20 PLang v2.0 Tokenizer
# Lexical analysis for policy language
"""
Tokenizer for PLang v2.0 with M19 category support.

Token types include:
- Keywords: policy, rule, when, then, deny, allow, etc.
- Categories: SAFETY, PRIVACY, OPERATIONAL, ROUTING, CUSTOM
- Identifiers: user-defined names
- Literals: numbers, strings, booleans
- Operators: ==, !=, <, >, etc.
- Delimiters: {, }, (, ), :, ,
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator, List, Optional


class TokenType(Enum):
    """Token types for PLang v2.0."""

    # Keywords
    POLICY = auto()
    RULE = auto()
    WHEN = auto()
    THEN = auto()
    IMPORT = auto()
    DENY = auto()
    ALLOW = auto()
    ESCALATE = auto()
    ROUTE = auto()
    TO = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    TRUE = auto()
    FALSE = auto()
    PRIORITY = auto()

    # M19 Categories
    SAFETY = auto()
    PRIVACY = auto()
    OPERATIONAL = auto()
    ROUTING = auto()
    CUSTOM = auto()

    # Literals
    IDENT = auto()
    NUMBER = auto()
    STRING = auto()

    # Operators
    EQ = auto()  # ==
    NE = auto()  # !=
    LT = auto()  # <
    GT = auto()  # >
    LE = auto()  # <=
    GE = auto()  # >=

    # Delimiters
    LBRACE = auto()  # {
    RBRACE = auto()  # }
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    COLON = auto()  # :
    COMMA = auto()  # ,
    DOT = auto()  # .

    # Special
    NEWLINE = auto()
    EOF = auto()
    COMMENT = auto()


# Keyword to token type mapping
KEYWORD_TOKENS = {
    "policy": TokenType.POLICY,
    "rule": TokenType.RULE,
    "when": TokenType.WHEN,
    "then": TokenType.THEN,
    "import": TokenType.IMPORT,
    "deny": TokenType.DENY,
    "allow": TokenType.ALLOW,
    "escalate": TokenType.ESCALATE,
    "route": TokenType.ROUTE,
    "to": TokenType.TO,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "priority": TokenType.PRIORITY,
    # Categories
    "SAFETY": TokenType.SAFETY,
    "PRIVACY": TokenType.PRIVACY,
    "OPERATIONAL": TokenType.OPERATIONAL,
    "ROUTING": TokenType.ROUTING,
    "CUSTOM": TokenType.CUSTOM,
}


@dataclass
class Token:
    """A token in PLang source code."""

    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:{self.column})"

    @property
    def is_category(self) -> bool:
        """Check if token is a category."""
        return self.type in {
            TokenType.SAFETY,
            TokenType.PRIVACY,
            TokenType.OPERATIONAL,
            TokenType.ROUTING,
            TokenType.CUSTOM,
        }

    @property
    def is_action(self) -> bool:
        """Check if token is an action."""
        return self.type in {TokenType.DENY, TokenType.ALLOW, TokenType.ESCALATE, TokenType.ROUTE}


class TokenizerError(Exception):
    """Error during tokenization."""

    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Tokenizer error at L{line}:{column}: {message}")


class Tokenizer:
    """
    Tokenizer for PLang v2.0.

    Converts source code into a stream of tokens for parsing.
    Supports M19 governance categories and policy-specific syntax.
    """

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    @property
    def current_char(self) -> Optional[str]:
        """Get current character or None if at end."""
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]

    def peek(self, offset: int = 1) -> Optional[str]:
        """Peek ahead by offset characters."""
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]

    def advance(self) -> str:
        """Advance to next character."""
        char = self.current_char
        self.pos += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char or ""

    def skip_whitespace(self) -> None:
        """Skip whitespace characters (except newlines for statement separation)."""
        while self.current_char and self.current_char in " \t\r":
            self.advance()

    def skip_comment(self) -> None:
        """Skip single-line comments starting with #."""
        if self.current_char == "#":
            while self.current_char and self.current_char != "\n":
                self.advance()

    def read_string(self) -> Token:
        """Read a string literal."""
        start_line = self.line
        start_col = self.column
        quote = self.advance()  # consume opening quote
        value = ""

        while self.current_char and self.current_char != quote:
            if self.current_char == "\\":
                self.advance()
                escape_char = self.advance()
                escape_map = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'"}
                value += escape_map.get(escape_char, escape_char)
            else:
                value += self.advance()

        if not self.current_char:
            raise TokenizerError("Unterminated string literal", start_line, start_col)

        self.advance()  # consume closing quote
        return Token(TokenType.STRING, value, start_line, start_col)

    def read_number(self) -> Token:
        """Read a number literal."""
        start_line = self.line
        start_col = self.column
        value = ""

        while self.current_char and (self.current_char.isdigit() or self.current_char == "."):
            value += self.advance()

        return Token(TokenType.NUMBER, value, start_line, start_col)

    def read_identifier(self) -> Token:
        """Read an identifier or keyword."""
        start_line = self.line
        start_col = self.column
        value = ""

        while self.current_char and (self.current_char.isalnum() or self.current_char == "_"):
            value += self.advance()

        # Check if it's a keyword
        token_type = KEYWORD_TOKENS.get(value, TokenType.IDENT)
        return Token(token_type, value, start_line, start_col)

    def read_operator(self) -> Token:
        """Read an operator."""
        start_line = self.line
        start_col = self.column
        char = self.current_char

        # Caller (tokenize) guarantees char is not None
        if char is None:
            raise TokenizerError("Unexpected end of input", start_line, start_col)

        # Two-character operators
        if char in "=!<>":
            next_char = self.peek()
            if next_char == "=":
                self.advance()
                self.advance()
                op_map = {"=": TokenType.EQ, "!": TokenType.NE, "<": TokenType.LE, ">": TokenType.GE}
                return Token(op_map[char], char + "=", start_line, start_col)
            elif char in "<>":
                self.advance()
                return Token(TokenType.LT if char == "<" else TokenType.GT, char, start_line, start_col)

        # Single-character operators and delimiters
        self.advance()
        token_map = {
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            ":": TokenType.COLON,
            ",": TokenType.COMMA,
            ".": TokenType.DOT,
        }

        if char in token_map:
            return Token(token_map[char], char, start_line, start_col)

        raise TokenizerError(f"Unexpected character: {char!r}", start_line, start_col)

    def tokenize(self) -> List[Token]:
        """
        Tokenize the source code.

        Returns:
            List of tokens including EOF.
        """
        self.tokens = []

        while self.current_char:
            self.skip_whitespace()

            if not self.current_char:
                break

            # Skip comments
            if self.current_char == "#":
                self.skip_comment()
                continue

            # Newlines
            if self.current_char == "\n":
                self.advance()
                continue

            # String literals
            if self.current_char in "\"'":
                self.tokens.append(self.read_string())
                continue

            # Numbers
            if self.current_char.isdigit():
                self.tokens.append(self.read_number())
                continue

            # Identifiers and keywords
            if self.current_char.isalpha() or self.current_char == "_":
                self.tokens.append(self.read_identifier())
                continue

            # Operators and delimiters
            if self.current_char in "=!<>{}():,.":
                self.tokens.append(self.read_operator())
                continue

            raise TokenizerError(f"Unexpected character: {self.current_char!r}", self.line, self.column)

        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

    def __iter__(self) -> Iterator[Token]:
        """Iterate over tokens."""
        if not self.tokens:
            self.tokenize()
        return iter(self.tokens)
