# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: AST Loader and Analyzer
# Authority: None (observational only)
# Callers: semantic_auditor.signals
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
AST Loader

Loads Python AST and extracts structural information:
- Async function definitions
- Import statements
- Function calls
- Class definitions
"""

import ast
from pathlib import Path
from typing import Optional, List, Tuple, NamedTuple
from dataclasses import dataclass, field


class ImportInfo(NamedTuple):
    """Information about an import statement."""

    module: str
    names: List[str]
    is_from_import: bool
    line_number: int


class FunctionInfo(NamedTuple):
    """Information about a function definition."""

    name: str
    is_async: bool
    line_number: int
    decorators: List[str]
    calls: List[str]


class CallInfo(NamedTuple):
    """Information about a function call."""

    name: str
    line_number: int
    in_async_context: bool


@dataclass
class ASTAnalysis:
    """Complete AST analysis result for a file."""

    file_path: Path
    parse_success: bool
    parse_error: Optional[str] = None
    imports: List[ImportInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    async_functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    top_level_calls: List[CallInfo] = field(default_factory=list)
    module_docstring: Optional[str] = None
    header_comments: List[str] = field(default_factory=list)

    @property
    def has_async_code(self) -> bool:
        """Check if file contains async code."""
        return len(self.async_functions) > 0


class CallVisitor(ast.NodeVisitor):
    """Visitor to extract function calls within a function body."""

    def __init__(self):
        self.calls: List[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        """Visit a Call node."""
        call_name = self._get_call_name(node.func)
        if call_name:
            self.calls.append(call_name)
        self.generic_visit(node)

    def _get_call_name(self, node: ast.expr) -> Optional[str]:
        """Extract the name from a call expression."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # Handle chained attributes like requests.get, session.commit
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return None


class ASTLoader:
    """Loads and analyzes Python AST."""

    def __init__(self):
        """Initialize the AST loader."""
        pass

    def load(self, file_path: Path) -> ASTAnalysis:
        """
        Load and analyze a Python file's AST.

        Args:
            file_path: Path to the Python file

        Returns:
            ASTAnalysis with extracted information
        """
        try:
            source = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError) as e:
            return ASTAnalysis(
                file_path=file_path,
                parse_success=False,
                parse_error=f"Failed to read file: {e}",
            )

        # Extract header comments before parsing
        header_comments = self._extract_header_comments(source)

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            return ASTAnalysis(
                file_path=file_path,
                parse_success=False,
                parse_error=f"Syntax error at line {e.lineno}: {e.msg}",
                header_comments=header_comments,
            )

        analysis = ASTAnalysis(
            file_path=file_path,
            parse_success=True,
            header_comments=header_comments,
        )

        # Extract module docstring
        analysis.module_docstring = ast.get_docstring(tree)

        # Walk the AST
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self._process_import(node, analysis)
            elif isinstance(node, ast.ImportFrom):
                self._process_import_from(node, analysis)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._process_function(node, analysis)
            elif isinstance(node, ast.ClassDef):
                analysis.classes.append(node.name)

        # Extract top-level calls (import-time side effects)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call_name = self._get_call_name(node.value.func)
                if call_name:
                    analysis.top_level_calls.append(
                        CallInfo(
                            name=call_name,
                            line_number=node.lineno,
                            in_async_context=False,
                        )
                    )

        return analysis

    def _extract_header_comments(self, source: str) -> List[str]:
        """Extract comment lines from the file header."""
        comments = []
        lines = source.split("\n")

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                comments.append(stripped)
            elif (
                stripped
                and not stripped.startswith('"""')
                and not stripped.startswith("'''")
            ):
                # Stop at first non-comment, non-empty line (unless it's a docstring)
                break
            elif stripped.startswith('"""') or stripped.startswith("'''"):
                # Skip docstrings at the top
                break

        return comments

    def _process_import(self, node: ast.Import, analysis: ASTAnalysis) -> None:
        """Process an import statement."""
        for alias in node.names:
            analysis.imports.append(
                ImportInfo(
                    module=alias.name,
                    names=[alias.asname or alias.name],
                    is_from_import=False,
                    line_number=node.lineno,
                )
            )

    def _process_import_from(self, node: ast.ImportFrom, analysis: ASTAnalysis) -> None:
        """Process a from-import statement."""
        module = node.module or ""
        names = [alias.name for alias in node.names]
        analysis.imports.append(
            ImportInfo(
                module=module,
                names=names,
                is_from_import=True,
                line_number=node.lineno,
            )
        )

    def _process_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, analysis: ASTAnalysis
    ) -> None:
        """Process a function definition."""
        is_async = isinstance(node, ast.AsyncFunctionDef)

        # Extract decorator names
        decorators = []
        for dec in node.decorator_list:
            dec_name = self._get_decorator_name(dec)
            if dec_name:
                decorators.append(dec_name)

        # Extract calls within the function
        call_visitor = CallVisitor()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_visitor.visit_Call(child)

        func_info = FunctionInfo(
            name=node.name,
            is_async=is_async,
            line_number=node.lineno,
            decorators=decorators,
            calls=call_visitor.calls,
        )

        analysis.functions.append(func_info)
        if is_async:
            analysis.async_functions.append(func_info)

    def _get_decorator_name(self, node: ast.expr) -> Optional[str]:
        """Extract decorator name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_call_name(node)
        elif isinstance(node, ast.Call):
            return self._get_call_name(node.func)
        return None

    def _get_call_name(self, node: ast.expr) -> Optional[str]:
        """Extract the name from a call expression."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return None

    def get_imports_from_module(
        self, analysis: ASTAnalysis, module_prefix: str
    ) -> List[ImportInfo]:
        """Get all imports from a specific module prefix."""
        return [imp for imp in analysis.imports if imp.module.startswith(module_prefix)]

    def get_async_functions_with_call(
        self, analysis: ASTAnalysis, call_pattern: str
    ) -> List[Tuple[FunctionInfo, str]]:
        """Find async functions that contain a specific call pattern."""
        import re

        pattern = re.compile(call_pattern)
        results = []

        for func in analysis.async_functions:
            for call in func.calls:
                if pattern.search(call):
                    results.append((func, call))

        return results
