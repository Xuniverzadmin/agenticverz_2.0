# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Pass 1 - Layer & Boundary Indexing
# Callers: sce_runner.py
# Allowed Imports: L6 (stdlib only), L8
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: SCE_CONTRACT.yaml

"""
Pass 1: Layer & Boundary Indexing

Operations:
  - assign_file_to_layer
  - build_import_graph
  - detect_boundary_crossings

Emits:
  - BOUNDARY_CROSSING_OBSERVED

This pass is READ-ONLY. It does not modify any files.
"""

import ast
import os
import re
from typing import Dict, List, Optional, Tuple


# Layer definitions based on SESSION_PLAYBOOK.yaml
LAYER_DEFINITIONS = {
    "L1": "Product Experience (UI)",
    "L2": "Product APIs",
    "L3": "Boundary Adapters",
    "L4": "Domain Engines",
    "L5": "Execution & Workers",
    "L6": "Platform Substrate",
    "L7": "Ops & Deployment",
    "L8": "Catalyst / Meta",
}

# Path-based layer heuristics
PATH_LAYER_HEURISTICS = [
    # L1 - UI
    (r"website/.*", "L1"),
    (r"frontend/.*", "L1"),
    (r"console/.*", "L1"),
    (r".*/components/.*", "L1"),
    (r".*/pages/.*", "L1"),
    # L2 - APIs
    (r".*/api/.*", "L2"),
    (r".*/routers?/.*", "L2"),
    (r".*/endpoints?/.*", "L2"),
    # L3 - Adapters
    (r".*/adapters?/.*", "L3"),
    (r".*/boundary/.*", "L3"),
    # L4 - Domain
    (r".*/domain/.*", "L4"),
    (r".*/engines?/.*", "L4"),
    (r".*/services?/.*", "L4"),
    (r".*/commands?/.*", "L4"),
    (r".*/planners?/.*", "L4"),
    # L5 - Workers
    (r".*/workers?/.*", "L5"),
    (r".*/execution/.*", "L5"),
    (r".*/runtime/.*", "L5"),
    (r".*/pool\.py$", "L5"),
    (r".*/runner\.py$", "L5"),
    # L6 - Platform
    (r".*/db\.py$", "L6"),
    (r".*/database/.*", "L6"),
    (r".*/events/.*", "L6"),
    (r".*/redis/.*", "L6"),
    (r".*/models?\.py$", "L6"),
    # L7 - Ops
    (r".*/ops/.*", "L7"),
    (r".*/deploy/.*", "L7"),
    (r".*/monitoring/.*", "L7"),
    (r"docker-compose.*", "L7"),
    (r"Dockerfile.*", "L7"),
    (r".*/systemd/.*", "L7"),
    # L8 - Catalyst
    (r".*/tests?/.*", "L8"),
    (r".*/ci/.*", "L8"),
    (r"\.github/.*", "L8"),
    (r".*/scripts/.*", "L8"),
    (r".*/validators?/.*", "L8"),
]


def extract_layer_from_metadata(
    file_path: str, content: str
) -> Optional[Tuple[str, str]]:
    """
    Extract layer declaration from file header metadata.

    Returns: Tuple of (layer, confidence) or None if not found
    """
    # Look for structured header comment
    # Pattern: # Layer: L{X} — {Name}
    layer_pattern = r"#\s*Layer:\s*(L[1-8])\s*[-—]\s*(.+)"

    for line in content.split("\n")[:30]:  # Only check first 30 lines
        match = re.match(layer_pattern, line)
        if match:
            layer = match.group(1)
            return (layer, "HIGH")

    return None


def infer_layer_from_path(file_path: str) -> Tuple[str, str]:
    """
    Infer layer from file path using heuristics.

    Returns: Tuple of (layer, confidence)
    """
    normalized_path = file_path.replace("\\", "/")

    for pattern, layer in PATH_LAYER_HEURISTICS:
        if re.search(pattern, normalized_path, re.IGNORECASE):
            return (layer, "HEURISTIC")

    return ("UNKNOWN", "LOW")


def assign_file_to_layer(file_path: str, content: str) -> Dict:
    """
    Assign a file to a layer based on metadata or path heuristics.
    """
    # Try metadata first
    metadata_result = extract_layer_from_metadata(file_path, content)
    if metadata_result:
        layer, confidence = metadata_result
        return {
            "file_path": file_path,
            "layer": layer,
            "confidence": confidence,
            "source": "metadata",
        }

    # Fall back to path heuristics
    layer, confidence = infer_layer_from_path(file_path)
    return {
        "file_path": file_path,
        "layer": layer,
        "confidence": confidence,
        "source": "path_heuristic",
    }


def extract_imports(file_path: str, content: str) -> List[Dict]:
    """
    Extract import statements from a Python file using AST.

    Returns list of import info dicts.
    """
    imports = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    {
                        "module": alias.name,
                        "line_number": node.lineno,
                        "import_type": "import",
                    }
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(
                    {
                        "module": module,
                        "name": alias.name,
                        "line_number": node.lineno,
                        "import_type": "from",
                    }
                )

    return imports


def resolve_import_to_file(
    import_module: str,
    repo_root: str,
    source_file: str,
) -> Optional[str]:
    """
    Attempt to resolve an import to a file path in the repo.

    This is a best-effort heuristic - not all imports can be resolved.
    """
    # Convert module path to file path
    module_path = import_module.replace(".", "/")

    # Common base directories
    base_dirs = ["backend", "sdk/python", "website", "scripts"]

    for base in base_dirs:
        # Try as package
        candidate = os.path.join(repo_root, base, module_path, "__init__.py")
        if os.path.exists(candidate):
            return os.path.relpath(candidate, repo_root)

        # Try as module
        candidate = os.path.join(repo_root, base, f"{module_path}.py")
        if os.path.exists(candidate):
            return os.path.relpath(candidate, repo_root)

    # Try from repo root
    candidate = os.path.join(repo_root, module_path, "__init__.py")
    if os.path.exists(candidate):
        return os.path.relpath(candidate, repo_root)

    candidate = os.path.join(repo_root, f"{module_path}.py")
    if os.path.exists(candidate):
        return os.path.relpath(candidate, repo_root)

    return None


def build_import_graph(
    files: Dict[str, str],
    layer_assignments: Dict[str, Dict],
    repo_root: str,
) -> Dict[str, List[str]]:
    """
    Build an import graph showing which files import which.

    Returns: Dict mapping file paths to list of imported file paths
    """
    graph = {}

    for file_path, content in files.items():
        if not file_path.endswith(".py"):
            continue

        imports = extract_imports(file_path, content)
        resolved_imports = []

        for imp in imports:
            module = imp["module"]
            if module:
                resolved = resolve_import_to_file(module, repo_root, file_path)
                if resolved and resolved in files:
                    resolved_imports.append(resolved)

        graph[file_path] = list(set(resolved_imports))

    return graph


def detect_boundary_crossings(
    import_graph: Dict[str, List[str]],
    layer_assignments: Dict[str, Dict],
    files: Dict[str, str],
) -> List[Dict]:
    """
    Detect imports that cross layer boundaries.

    Emits: BOUNDARY_CROSSING_OBSERVED
    """
    crossings = []

    for from_file, imports in import_graph.items():
        from_assignment = layer_assignments.get(from_file, {})
        from_layer = from_assignment.get("layer", "UNKNOWN")

        for to_file in imports:
            to_assignment = layer_assignments.get(to_file, {})
            to_layer = to_assignment.get("layer", "UNKNOWN")

            # Only record actual crossings (different layers)
            if (
                from_layer != to_layer
                and from_layer != "UNKNOWN"
                and to_layer != "UNKNOWN"
            ):
                # Find the line number of this import
                line_number = None
                if from_file in files:
                    content = files[from_file]
                    imports_list = extract_imports(from_file, content)
                    for imp in imports_list:
                        resolved = resolve_import_to_file(
                            imp["module"],
                            "",  # Not needed for matching
                            from_file,
                        )
                        # Simplified matching
                        if imp["module"] and imp["module"].split(".")[-1] in to_file:
                            line_number = imp["line_number"]
                            break

                crossings.append(
                    {
                        "from_file": from_file,
                        "to_file": to_file,
                        "from_layer": from_layer,
                        "to_layer": to_layer,
                        "crossing_type": "import",
                        "line_number": line_number,
                    }
                )

    return crossings


def run_pass_1(repo_root: str, files: Dict[str, str]) -> Dict:
    """
    Execute Pass 1: Layer & Boundary Indexing.

    Args:
        repo_root: Absolute path to repository root
        files: Dict mapping relative file paths to file contents

    Returns:
        Pass 1 output dict containing:
        - layer_assignments
        - import_graph
        - boundary_crossings
    """
    # Step 1: Assign files to layers
    layer_assignments = {}
    layer_assignments_list = []

    for file_path, content in files.items():
        if file_path.endswith(".py"):
            assignment = assign_file_to_layer(file_path, content)
            layer_assignments[file_path] = assignment
            layer_assignments_list.append(assignment)

    # Step 2: Build import graph
    import_graph = build_import_graph(files, layer_assignments, repo_root)

    # Step 3: Detect boundary crossings
    boundary_crossings = detect_boundary_crossings(
        import_graph,
        layer_assignments,
        files,
    )

    return {
        "layer_assignments": layer_assignments_list,
        "import_graph": import_graph,
        "boundary_crossings": boundary_crossings,
    }
