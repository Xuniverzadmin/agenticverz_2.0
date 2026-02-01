#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Extract L2 (Product API) endpoints from the AOS/AgenticVerz backend.
# artifact_class: CODE
"""
Extract L2 (Product API) endpoints from the AOS/AgenticVerz backend.

This script parses all API router files and extracts:
- HTTP method
- Route path
- Function name
- Input signals (path params, query params, request body)
- Output signals (response model)
- Description

Output: CSV file with all L2 endpoints

Layer: L8 - Catalyst / Meta
Product: system-wide
"""

import ast
import csv
import re
from pathlib import Path
from typing import List, Tuple


class EndpointInfo:
    """Represents a single API endpoint."""

    def __init__(
        self,
        file_name: str = "",
        router_prefix: str = "",
        http_method: str = "",
        route_path: str = "",
        full_path: str = "",
        function_name: str = "",
        input_path_params: str = "",
        input_query_params: str = "",
        input_body_model: str = "",
        output_model: str = "",
        description: str = "",
        tags: str = "",
        layer: str = "L2",
    ):
        self.file_name = file_name
        self.router_prefix = router_prefix
        self.http_method = http_method
        self.route_path = route_path
        self.full_path = full_path
        self.function_name = function_name
        self.input_path_params = input_path_params
        self.input_query_params = input_query_params
        self.input_body_model = input_body_model
        self.output_model = output_model
        self.description = description
        self.tags = tags
        self.layer = layer


def extract_router_prefix(content: str) -> str:
    """Extract the router prefix from APIRouter instantiation."""
    match = re.search(r'APIRouter\s*\([^)]*prefix\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    return ""


def extract_tags(content: str) -> str:
    """Extract tags from APIRouter instantiation."""
    match = re.search(r"APIRouter\s*\([^)]*tags\s*=\s*\[([^\]]+)\]", content)
    if match:
        tags_str = match.group(1)
        tags = re.findall(r'["\']([^"\']+)["\']', tags_str)
        return ", ".join(tags)
    return ""


def extract_docstring(node) -> str:
    """Extract the first line of a function's docstring."""
    docstring = ast.get_docstring(node)
    if docstring:
        first_line = docstring.split("\n")[0].strip()
        first_line = first_line.replace('"', "'")
        return first_line[:200]
    return ""


def extract_response_model(decorator: ast.Call) -> str:
    """Extract response_model from a route decorator."""
    for keyword in decorator.keywords:
        if keyword.arg == "response_model":
            try:
                return ast.unparse(keyword.value)
            except Exception:
                if isinstance(keyword.value, ast.Name):
                    return keyword.value.id
    return ""


def extract_path_params(route: str) -> str:
    """Extract path parameters from route string."""
    if not isinstance(route, str):
        return ""
    params = re.findall(r"\{([^}]+)\}", route)
    return ", ".join(params) if params else ""


def extract_function_params(node) -> Tuple[str, str]:
    """Extract query params and body model from function signature."""
    query_params = []
    body_model = ""

    skip_args = {
        "self",
        "request",
        "session",
        "_rate_limited",
        "_tier",
        "auth",
        "ctx",
        "token",
        "_http_request",
    }

    for arg in node.args.args:
        arg_name = arg.arg
        if arg_name in skip_args:
            continue

        if arg.annotation:
            try:
                ann_str = ast.unparse(arg.annotation)
            except Exception:
                ann_str = ""

            # Check if it's a Query parameter
            if "Query" in ann_str or arg_name in (
                "limit",
                "offset",
                "tenant_id",
                "level",
                "include_",
            ):
                query_params.append(arg_name)
            # Check if it's a body model (capitalized, likely Pydantic)
            elif (
                ann_str
                and ann_str[0].isupper()
                and "Request" not in ann_str
                and "Session" not in ann_str
            ):
                if "Depends" not in ann_str and "Token" not in ann_str:
                    body_model = ann_str

    return ", ".join(query_params), body_model


def parse_api_file(file_path: Path) -> List[EndpointInfo]:
    """Parse a single API file and extract endpoint information."""
    endpoints = []

    try:
        content = file_path.read_text()
        tree = ast.parse(content)
    except Exception as e:
        print(f"  Error parsing {file_path}: {e}")
        return endpoints

    router_prefix = extract_router_prefix(content)
    tags = extract_tags(content)
    file_name = file_path.name

    # Determine layer from file header comments
    layer = "L2"
    if "# Layer: L2a" in content:
        layer = "L2a (Console-scoped)"
    elif "# Layer: L2" in content:
        layer = "L2 (Product APIs)"

    for node in ast.walk(tree):
        # Handle both FunctionDef and AsyncFunctionDef
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                http_method = None
                route = ""
                response_model = ""

                # Handle @router.get("/path") or @router.post("/path", response_model=...)
                if isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Attribute):
                        method_name = decorator.func.attr.upper()
                        if method_name in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                            http_method = method_name

                            # Extract route from first positional arg
                            if decorator.args and isinstance(
                                decorator.args[0], ast.Constant
                            ):
                                route = str(decorator.args[0].value)

                            # Get response model
                            response_model = extract_response_model(decorator)

                # Handle @app.get("/path") from main.py
                elif isinstance(decorator, ast.Attribute):
                    method_name = decorator.attr.upper()
                    if method_name in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                        http_method = method_name

                if http_method and route:
                    # Get path params
                    path_params = extract_path_params(route)

                    # Get query params and body model
                    query_params, body_model = extract_function_params(node)

                    # Get description from docstring
                    description = extract_docstring(node)

                    # Build full path
                    full_path = router_prefix + route if router_prefix else route

                    endpoints.append(
                        EndpointInfo(
                            file_name=file_name,
                            router_prefix=router_prefix,
                            http_method=http_method,
                            route_path=route,
                            full_path=full_path,
                            function_name=node.name,
                            input_path_params=path_params,
                            input_query_params=query_params,
                            input_body_model=body_model,
                            output_model=response_model,
                            description=description,
                            tags=tags,
                            layer=layer,
                        )
                    )

    return endpoints


def main():
    """Main function to extract all L2 endpoints."""
    api_dir = Path("/root/agenticverz2.0/backend/app/api")

    if not api_dir.exists():
        print("Error: API directory not found:", api_dir)
        return

    all_endpoints = []

    # Get all Python files in the api directory
    api_files = [
        f
        for f in api_dir.glob("*.py")
        if not f.name.startswith("__")
        and "dependencies" not in f.name
        and "middleware" not in str(f)
        and "helpers" not in f.name
        and "protection" not in f.name
        and "billing" not in f.name
    ]

    print(f"Found {len(api_files)} API files to parse")

    for api_file in sorted(api_files):
        print(f"  Parsing: {api_file.name}")
        endpoints = parse_api_file(api_file)
        all_endpoints.extend(endpoints)
        print(f"    Found {len(endpoints)} endpoints")

    # Also check main.py for additional endpoints
    main_py = Path("/root/agenticverz2.0/backend/app/main.py")
    if main_py.exists():
        print("  Parsing: main.py")
        main_endpoints = parse_api_file(main_py)
        all_endpoints.extend(main_endpoints)
        print(f"    Found {len(main_endpoints)} endpoints")

    print(f"\nTotal endpoints found: {len(all_endpoints)}")

    # Write to CSV
    output_path = Path("/root/agenticverz2.0/docs/api/L2_API_ENDPOINTS.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(
            [
                "Layer",
                "File",
                "HTTP Method",
                "Full Path",
                "Function Name",
                "Path Parameters (Input)",
                "Query Parameters (Input)",
                "Request Body Model (Input)",
                "Response Model (Output)",
                "Tags",
                "Description",
            ]
        )

        # Sort by full path for better organization
        all_endpoints.sort(key=lambda x: (x.full_path, x.http_method))

        for ep in all_endpoints:
            writer.writerow(
                [
                    ep.layer,
                    ep.file_name,
                    ep.http_method,
                    ep.full_path,
                    ep.function_name,
                    ep.input_path_params,
                    ep.input_query_params,
                    ep.input_body_model,
                    ep.output_model,
                    ep.tags,
                    ep.description,
                ]
            )

    print(f"\nCSV written to: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    main()
