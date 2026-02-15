#!/usr/bin/env python3
# Layer: L8
# AUDIENCE: INTERNAL
# Role: Generate a lazy-load skills registry markdown from installed Codex skills.

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
NAME_RE = re.compile(r"^name:\s*(.+)$", re.MULTILINE)
DESC_RE = re.compile(r"^description:\s*(.+)$", re.MULTILINE)


@dataclass
class SkillMeta:
    name: str
    description: str
    path: Path
    is_system: bool


def parse_skill_md(skill_md: Path) -> SkillMeta | None:
    text = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.search(text)
    if not match:
        return None

    frontmatter = match.group(1)
    name_match = NAME_RE.search(frontmatter)
    desc_match = DESC_RE.search(frontmatter)
    if not name_match or not desc_match:
        return None

    name = name_match.group(1).strip().strip('"').strip("'")
    description = desc_match.group(1).strip().strip('"').strip("'")
    is_system = "/.system/" in str(skill_md)
    return SkillMeta(name=name, description=description, path=skill_md, is_system=is_system)


def discover_skills(skills_root: Path, include_system: bool) -> list[SkillMeta]:
    skills: list[SkillMeta] = []
    for skill_md in sorted(skills_root.glob("**/SKILL.md")):
        meta = parse_skill_md(skill_md)
        if not meta:
            continue
        if meta.is_system and not include_system:
            continue
        skills.append(meta)
    return skills


def load_mapping(mapping_file: Path) -> dict[str, Any]:
    if not mapping_file.exists():
        raise FileNotFoundError(f"mapping file not found: {mapping_file}")
    return json.loads(mapping_file.read_text(encoding="utf-8"))


def render_registry(
    skills: list[SkillMeta],
    mapping: dict[str, Any],
    skills_root: Path,
    mapping_file: Path,
) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines: list[str] = []
    lines.append("# Codex Skills Registry")
    lines.append("")
    lines.append("Generated artifact for lazy-load skill discovery. Do not hardcode full skill loads in bootstrap.")
    lines.append("")
    lines.append(f"- Generated: `{generated_at}`")
    lines.append(f"- Skills root: `{skills_root}`")
    lines.append(f"- Intent map: `{mapping_file}`")
    lines.append("")
    lines.append("## Installed Skills")
    lines.append("")
    lines.append("| Skill | Description | Path | Type |")
    lines.append("|------|-------------|------|------|")
    for skill in skills:
        skill_type = "system" if skill.is_system else "project"
        lines.append(
            f"| `{skill.name}` | {skill.description} | `{skill.path}` | {skill_type} |"
        )
    lines.append("")
    lines.append("## Intent to Skill Mapping")
    lines.append("")
    lines.append("Lazy-load rule: match intent first, then load only selected skill `SKILL.md`, and only needed references.")
    lines.append("")
    lines.append("| Intent ID | Match Any | Skill | Confidence |")
    lines.append("|-----------|-----------|-------|------------|")

    for rule in mapping.get("rules", []):
        intent_id = str(rule.get("intent_id", ""))
        match_any = ", ".join(f"`{x}`" for x in rule.get("match_any", []))
        skill = str(rule.get("skill", ""))
        confidence = str(rule.get("confidence", ""))
        lines.append(f"| `{intent_id}` | {match_any} | `{skill}` | {confidence} |")

    lines.append("")
    lines.append("## Activation Policy (Summary)")
    lines.append("")
    defaults = mapping.get("defaults", {})
    lines.append(f"- Activation mode: `{defaults.get('activation_mode', 'lazy')}`")
    lines.append(f"- Max skills per task: `{defaults.get('max_skills_per_task', 2)}`")
    lines.append(
        f"- Low confidence behavior: `{defaults.get('low_confidence_action', 'ask')}`"
    )
    lines.append(
        "- Never preload full skill bodies at bootstrap; load on-demand per task intent."
    )
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate lazy-load skills registry markdown.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root path.",
    )
    parser.add_argument(
        "--skills-root",
        type=Path,
        default=Path.home() / ".codex" / "skills",
        help="Installed Codex skills root.",
    )
    parser.add_argument(
        "--mapping-file",
        type=Path,
        default=None,
        help="Intent-to-skill mapping file (JSON). Default: <repo>/config/intent_skill_map.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output markdown path. Default: <repo>/docs/SKILLS_REGISTRY.md",
    )
    parser.add_argument(
        "--include-system",
        action="store_true",
        help="Include .system skills in output.",
    )

    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    skills_root = args.skills_root.resolve()
    mapping_file = (
        args.mapping_file.resolve()
        if args.mapping_file is not None
        else (repo_root / "config" / "intent_skill_map.json")
    )
    output_file = (
        args.output.resolve()
        if args.output is not None
        else (repo_root / "docs" / "SKILLS_REGISTRY.md")
    )

    if not skills_root.exists():
        raise FileNotFoundError(f"skills root not found: {skills_root}")

    skills = discover_skills(skills_root, include_system=args.include_system)
    mapping = load_mapping(mapping_file)
    content = render_registry(skills, mapping, skills_root, mapping_file)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(content, encoding="utf-8")
    print(f"generated: {output_file}")
    print(f"skills: {len(skills)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
