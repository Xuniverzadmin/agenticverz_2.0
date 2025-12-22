# M20 Policy IR Symbol Table
# Symbol management for policy compilation
"""
Symbol table for PLang v2.0 compilation.

Features:
- Hierarchical scoping (global, policy, rule, block)
- Category-aware symbol lookup
- Governance metadata tracking
- M19 policy reference resolution
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from app.policy.compiler.grammar import PolicyCategory


class SymbolType(Enum):
    """Types of symbols in PLang."""

    POLICY = auto()
    RULE = auto()
    VARIABLE = auto()
    PARAMETER = auto()
    FUNCTION = auto()
    CONSTANT = auto()
    IMPORT = auto()


@dataclass
class Symbol:
    """
    A symbol in the symbol table.

    Represents named entities in PLang: policies, rules, variables, etc.
    """

    name: str
    symbol_type: SymbolType
    category: Optional[PolicyCategory] = None
    priority: int = 50
    value_type: Optional[str] = None  # For typed symbols
    value: Any = None  # For constants
    defined_at: Optional[str] = None  # Source location
    referenced_by: List[str] = field(default_factory=list)
    # Governance
    requires_approval: bool = False
    audit_level: int = 0

    def __repr__(self) -> str:
        cat = f"[{self.category.value}]" if self.category else ""
        return f"Symbol({self.name}, {self.symbol_type.name}{cat})"


@dataclass
class Scope:
    """
    A scope in the symbol table.

    Scopes form a hierarchy: global -> policy -> rule -> block
    """

    name: str
    parent: Optional["Scope"] = None
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    children: List["Scope"] = field(default_factory=list)
    category: Optional[PolicyCategory] = None

    def define(self, symbol: Symbol) -> None:
        """Define a symbol in this scope."""
        if symbol.name in self.symbols:
            raise ValueError(f"Symbol '{symbol.name}' already defined in scope '{self.name}'")
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str, local_only: bool = False) -> Optional[Symbol]:
        """
        Look up a symbol by name.

        Args:
            name: Symbol name to find
            local_only: If True, only search this scope

        Returns:
            Symbol if found, None otherwise
        """
        if name in self.symbols:
            return self.symbols[name]
        if not local_only and self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_by_category(self, category: PolicyCategory) -> List[Symbol]:
        """Get all symbols in a category."""
        result = [s for s in self.symbols.values() if s.category == category]
        if self.parent:
            result.extend(self.parent.lookup_by_category(category))
        return result

    def get_all_symbols(self) -> Dict[str, Symbol]:
        """Get all visible symbols including parent scopes."""
        result = {}
        if self.parent:
            result.update(self.parent.get_all_symbols())
        result.update(self.symbols)
        return result


class SymbolTable:
    """
    Symbol table for PLang compilation.

    Manages scopes and symbol resolution with M19 category awareness.
    """

    def __init__(self):
        self.global_scope = Scope(name="global")
        self.current_scope = self.global_scope
        self._scope_stack: List[Scope] = [self.global_scope]

        # Category-indexed symbol lookup
        self._symbols_by_category: Dict[PolicyCategory, List[Symbol]] = {cat: [] for cat in PolicyCategory}

        # Built-in symbols
        self._define_builtins()

    def _define_builtins(self) -> None:
        """Define built-in symbols."""
        # Built-in functions available in PLang
        builtins = [
            ("contains", SymbolType.FUNCTION),
            ("startswith", SymbolType.FUNCTION),
            ("endswith", SymbolType.FUNCTION),
            ("len", SymbolType.FUNCTION),
            ("lower", SymbolType.FUNCTION),
            ("upper", SymbolType.FUNCTION),
            ("matches", SymbolType.FUNCTION),  # Regex match
            ("in_list", SymbolType.FUNCTION),
            ("is_empty", SymbolType.FUNCTION),
            # Context accessors
            ("ctx", SymbolType.VARIABLE),  # Execution context
            ("agent", SymbolType.VARIABLE),  # Current agent
            ("user", SymbolType.VARIABLE),  # Current user
            ("request", SymbolType.VARIABLE),  # Current request
            ("budget", SymbolType.VARIABLE),  # Budget info
        ]

        for name, sym_type in builtins:
            self.global_scope.define(
                Symbol(
                    name=name,
                    symbol_type=sym_type,
                    defined_at="builtin",
                )
            )

    def enter_scope(self, name: str, category: Optional[PolicyCategory] = None) -> Scope:
        """
        Enter a new scope.

        Args:
            name: Scope name
            category: Optional governance category

        Returns:
            The new scope
        """
        new_scope = Scope(
            name=name,
            parent=self.current_scope,
            category=category or self.current_scope.category,
        )
        self.current_scope.children.append(new_scope)
        self.current_scope = new_scope
        self._scope_stack.append(new_scope)
        return new_scope

    def exit_scope(self) -> Scope:
        """
        Exit current scope, returning to parent.

        Returns:
            The exited scope
        """
        if len(self._scope_stack) <= 1:
            raise ValueError("Cannot exit global scope")
        exited = self._scope_stack.pop()
        self.current_scope = self._scope_stack[-1]
        return exited

    def define(self, symbol: Symbol) -> None:
        """
        Define a symbol in current scope.

        Also indexes by category for governance lookup.
        """
        self.current_scope.define(symbol)
        if symbol.category:
            self._symbols_by_category[symbol.category].append(symbol)

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol by name."""
        return self.current_scope.lookup(name)

    def lookup_policy(self, name: str) -> Optional[Symbol]:
        """Look up a policy symbol specifically."""
        symbol = self.global_scope.lookup(name, local_only=True)
        if symbol and symbol.symbol_type == SymbolType.POLICY:
            return symbol
        return None

    def lookup_rule(self, name: str, policy: Optional[str] = None) -> Optional[Symbol]:
        """
        Look up a rule symbol.

        Args:
            name: Rule name
            policy: Optional policy name to search within
        """
        # Check current scope first
        symbol = self.current_scope.lookup(name)
        if symbol and symbol.symbol_type == SymbolType.RULE:
            return symbol

        # If policy specified, check its scope
        if policy:
            policy_sym = self.lookup_policy(policy)
            if policy_sym:
                # Find policy scope and search there
                for scope in self._scope_stack:
                    if scope.name == policy:
                        symbol = scope.lookup(name, local_only=True)
                        if symbol and symbol.symbol_type == SymbolType.RULE:
                            return symbol
        return None

    def get_symbols_by_category(
        self, category: PolicyCategory, symbol_type: Optional[SymbolType] = None
    ) -> List[Symbol]:
        """
        Get all symbols in a category.

        Args:
            category: Governance category
            symbol_type: Optional filter by symbol type

        Returns:
            List of matching symbols, sorted by priority
        """
        symbols = self._symbols_by_category.get(category, [])
        if symbol_type:
            symbols = [s for s in symbols if s.symbol_type == symbol_type]
        return sorted(symbols, key=lambda s: s.priority, reverse=True)

    def get_policies(self) -> List[Symbol]:
        """Get all policy symbols."""
        return [s for s in self.global_scope.symbols.values() if s.symbol_type == SymbolType.POLICY]

    def get_rules(self) -> List[Symbol]:
        """Get all rule symbols."""
        rules = []
        for cat_symbols in self._symbols_by_category.values():
            rules.extend(s for s in cat_symbols if s.symbol_type == SymbolType.RULE)
        return rules

    def add_reference(self, name: str, referenced_from: str) -> None:
        """Track a reference to a symbol."""
        symbol = self.lookup(name)
        if symbol:
            symbol.referenced_by.append(referenced_from)

    def get_unreferenced_symbols(self) -> List[Symbol]:
        """Get symbols that are never referenced (for dead code analysis)."""
        unreferenced = []
        for scope in self._scope_stack:
            for symbol in scope.symbols.values():
                if not symbol.referenced_by and symbol.defined_at != "builtin":
                    unreferenced.append(symbol)
        return unreferenced

    def __str__(self) -> str:
        lines = ["SymbolTable:"]
        for scope in self._scope_stack:
            lines.append(f"  Scope '{scope.name}':")
            for sym in scope.symbols.values():
                lines.append(f"    {sym}")
        return "\n".join(lines)
