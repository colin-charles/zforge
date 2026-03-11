"""zforge fix — auto-repair skill deficiencies so they pass validation."""
from __future__ import annotations

import json
import re
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from cli._console import HAS_RICH, console, _print, _rule
from cli._constants import VALID_CATEGORIES
from cli.validator import run_validate, REQUIRED_SECTIONS

# ---------------------------------------------------------------------------
# YAML-like frontmatter parser (no pyyaml dependency needed)
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """Extract YAML frontmatter from SKILL.md. Returns (metadata_dict, body)."""
    pattern = re.compile(r"^---\s*\n(.+?)\n---\s*\n", re.DOTALL)
    match = pattern.match(text)
    if not match:
        return {}, text

    raw_yaml = match.group(1)
    body = text[match.end():]

    if HAS_YAML:
        try:
            meta = yaml.safe_load(raw_yaml)
            return (meta if isinstance(meta, dict) else {}), body
        except Exception:
            pass

    # Fallback: simple key-value parser for common frontmatter
    meta: Dict[str, Any] = {}
    for line in raw_yaml.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip().strip('"').strip("'") 
        val = val.strip().strip('"').strip("'")
        # Handle YAML lists like ["a", "b"]
        if val.startswith("[") and val.endswith("]"):
            items = val[1:-1].split(",")
            meta[key] = [i.strip().strip('"').strip("'") for i in items if i.strip()]
        else:
            meta[key] = val
    return meta, body


def _find_sections(body: str) -> List[str]:
    """Return list of section names (lowercase) found in markdown body."""
    sections = []
    for match in re.finditer(r"^#{1,3}\s+(.+)", body, re.MULTILINE):
        sections.append(match.group(1).strip().lower())
    return sections


def _extract_section_content(body: str, section_name: str) -> str:
    """Extract content under a specific ## section header."""
    pattern = re.compile(
        r"^(#{1,3})\s+" + re.escape(section_name) + r"\s*\n(.*?)(?=^#{1,3}\s|\Z)",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(body)
    return match.group(2).strip() if match else ""


# ---------------------------------------------------------------------------
# Fixers
# ---------------------------------------------------------------------------

def _generate_skill_json(meta: Dict[str, Any], body: str, skill_dir: Path) -> dict:
    """Generate a full skill.json from SKILL.md frontmatter + content."""
    name = meta.get("name", skill_dir.name)
    slug = name.replace("_", "-").replace(" ", "-").lower()
    version = meta.get("version", "1.0.0")
    author = meta.get("author", "")
    description = meta.get("description", "")
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]

    # Determine category from tags or default
    category = meta.get("category", "skill")
    if category not in VALID_CATEGORIES:
        category = "skill"

    # Build short description (<=120 chars)
    short_desc = description[:120] if description else f"{name} skill for Agent Zero"

    # Build long description from overview section
    overview = _extract_section_content(body, "Overview")
    long_desc = overview[:500] if overview else description or f"A skill providing {name} capabilities."

    # Build agent description from overview + expertise
    expertise = _extract_section_content(body, "Expertise")
    agent_parts = []
    if description:
        agent_parts.append(description)
    if expertise:
        # Extract key terms from expertise bullets
        terms = re.findall(r"^[-*]\s+(.+?)(?::|$)", expertise, re.MULTILINE)
        if terms:
            agent_parts.append("Key capabilities: " + ", ".join(t.strip() for t in terms[:8]))
    agent_desc = " ".join(agent_parts) if agent_parts else f"Use this skill for {name} tasks."
    # Ensure minimum 10 words
    if len(agent_desc.split()) < 10:
        agent_desc += f" This skill helps agents handle {name}-related tasks effectively and reliably."

    now = datetime.now().strftime("%Y-%m-%d")

    # Detect scripts
    scripts_list = []
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.is_dir():
        for f in sorted(scripts_dir.rglob("*.py")):
            rel = f.relative_to(skill_dir)
            scripts_list.append({
                "filename": str(rel),
                "description": f"{f.stem} script",
                "entrypoint": len(scripts_list) == 0,
            })

    # Detect requirements
    pip_reqs = []
    req_file = skill_dir / "requirements.txt"
    if req_file.exists():
        for line in req_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                pip_reqs.append(line)

    return {
        "$schema": "https://zero-forge.org/schemas/skill-manifest/v1.0.0.json",
        "metadata": {
            "name": name,
            "slug": slug,
            "version": version,
            "author": author,
            "author_url": f"https://github.com/{author}" if author else "",
            "license": meta.get("license", "MIT"),
            "price": meta.get("price", "free"),
            "category": category,
            "tags": tags,
            "created_at": now,
            "updated_at": now,
        },
        "description": {
            "short": short_desc,
            "long": long_desc,
            "description_for_agent": agent_desc,
        },
        "compatibility": {
            "agentZero_min_version": "0.8.0",
            "agentZero_tested_versions": ["0.9.0"],
            "frameworks": ["agentZero"],
            "os": ["linux", "macos", "windows-wsl"],
            "python_min_version": "3.10",
        },
        "requirements": {
            "pip": pip_reqs,
            "apt": [],
            "env_vars": [],
            "system": "",
        },
        "files": {
            "skill_md": "SKILL.md",
            "install_script": "install.sh" if (skill_dir / "install.sh").exists() else None,
            "requirements_txt": "requirements.txt" if req_file.exists() else None,
            "scripts": scripts_list,
            "config": None,
        },
        "quality": {
            "apol_certified": False,
            "apol_cert_id": None,
            "apol_cert_issued_at": None,
            "apol_composite_score": None,
            "apol_cert_url": None,
        },
        "marketplace": {
            "listing_url": f"https://zero-forge.org/listing/{slug}",
            "featured": False,
            "downloads": 0,
            "stars": 0,
            "verified_publisher": False,
            "install_time_minutes": 5,
        },
        "install": {
            "one_liner": f"zforge install {slug}",
            "manual": "bash install.sh" if (skill_dir / "install.sh").exists() else f"Copy to agent skills directory",
        },
    }


def _generate_usage_section(meta: Dict[str, Any], body: str) -> str:
    """Generate a ## Usage section from existing SKILL.md content."""
    name = meta.get("name", "this skill")

    # Try to extract useful content from Process, Examples, or Expertise sections
    process = _extract_section_content(body, "Process")
    examples = _extract_section_content(body, "Examples")
    expertise = _extract_section_content(body, "Expertise")
    overview = _extract_section_content(body, "Overview")

    lines = ["## Usage\n"]

    if process:
        # Summarize the process into usage steps
        steps = re.findall(r"^###\s+\d+\.\s+(.+)", process, re.MULTILINE)
        if steps:
            lines.append(f"To use **{name}**, follow these steps:\n")
            for i, step in enumerate(steps, 1):
                lines.append(f"{i}. **{step.strip()}**")
            lines.append("")
        else:
            lines.append(f"Load this skill when you need {name} capabilities.\n")
    elif overview:
        lines.append(f"Load this skill when you need {name} capabilities.\n")
        # Extract key action items from overview
        bullets = re.findall(r"[-*]\s+(.+)", overview)
        if bullets:
            lines.append("This skill supports:\n")
            for b in bullets[:6]:
                lines.append(f"- {b.strip()}")
            lines.append("")

    if not process and not overview:
        lines.append(f"1. Load this skill when working on {name}-related tasks")
        lines.append(f"2. The agent will use the procedures and templates defined below")
        lines.append(f"3. Review generated output and iterate as needed\n")

    # Add a basic invocation example
    lines.append("### Quick Start\n")
    lines.append("```")
    lines.append(f"# Load the skill in Agent Zero")
    lines.append(f"# Ask: \"Use {name} to ...\"")
    lines.append("```\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main fix runner
# ---------------------------------------------------------------------------

def run_fix(skill_dir: str | Path | None = None, dry_run: bool = False) -> int:
    """Auto-fix skill deficiencies. Returns 0 on success, 1 on failure."""
    skill_dir = (Path(skill_dir) if skill_dir else Path.cwd()).resolve()

    _rule(f"zforge fix -- '{skill_dir.name}'")

    if not skill_dir.is_dir():
        _print(f"  [bold red]Directory not found: {skill_dir}[/bold red]")
        return 1

    # -- Read SKILL.md --------------------------------------------------------
    skill_md_path = skill_dir / "SKILL.md"
    if not skill_md_path.exists():
        _print("  [bold red]SKILL.md not found — cannot fix without it.[/bold red]")
        _print("  [dim]Hint: run 'zforge new <name>' to scaffold a skill from scratch.[/dim]")
        return 1

    content = skill_md_path.read_text(encoding="utf-8", errors="replace")
    meta, body = _parse_frontmatter(content)
    sections = _find_sections(body)

    fixes_applied = []
    fixes_preview = []

    # -- Fix 1: Missing skill.json -------------------------------------------
    skill_json_path = skill_dir / "skill.json"
    if not skill_json_path.exists():
        _print("  [yellow]ISSUE:[/yellow] skill.json not found")
        generated = _generate_skill_json(meta, body, skill_dir)
        if dry_run:
            _print("  [cyan]WOULD CREATE:[/cyan] skill.json")
            if HAS_RICH:
                from rich.syntax import Syntax
                console.print(Syntax(json.dumps(generated, indent=2), "json", theme="monokai", line_numbers=False))
            else:
                print(json.dumps(generated, indent=2))
            fixes_preview.append("skill.json")
        else:
            skill_json_path.write_text(json.dumps(generated, indent=2))
            _print("  [green]FIXED:[/green] Generated skill.json from SKILL.md frontmatter")
            fixes_applied.append("skill.json")
    else:
        _print("  [green]OK:[/green] skill.json exists")
        # Check for missing required fields
        try:
            data = json.loads(skill_json_path.read_text())
            m = data.get("metadata", data)
            missing_fields = []
            for field in ("name", "version", "description", "author", "category"):
                if not m.get(field, data.get(field, "")):
                    missing_fields.append(field)
            if missing_fields:
                _print(f"  [yellow]ISSUE:[/yellow] skill.json missing fields: {', '.join(missing_fields)}")
                # Patch from frontmatter
                if not dry_run:
                    if "metadata" not in data:
                        data["metadata"] = {}
                    fm_map = {
                        "name": meta.get("name", skill_dir.name),
                        "version": meta.get("version", "1.0.0"),
                        "author": meta.get("author", ""),
                        "category": meta.get("category", "skill"),
                    }
                    desc = meta.get("description", "")
                    if "description" in missing_fields:
                        if isinstance(data.get("description"), dict):
                            data["description"]["short"] = desc[:120]
                        else:
                            data["metadata"]["description"] = desc[:120]
                    for f in missing_fields:
                        if f != "description" and f in fm_map:
                            data["metadata"][f] = fm_map[f]
                    skill_json_path.write_text(json.dumps(data, indent=2))
                    _print(f"  [green]FIXED:[/green] Patched missing fields in skill.json")
                    fixes_applied.append("skill.json (patched)")
                else:
                    _print(f"  [cyan]WOULD PATCH:[/cyan] {', '.join(missing_fields)} in skill.json")
                    fixes_preview.append("skill.json (patch)")
        except json.JSONDecodeError as exc:
            _print(f"  [bold red]skill.json is invalid JSON: {exc}[/bold red]")
            _print("  [dim]Manual fix required — cannot auto-repair broken JSON[/dim]")

    # -- Fix 2: Missing required sections in SKILL.md -------------------------
    for section in REQUIRED_SECTIONS:
        if section not in sections:
            _print(f"  [yellow]ISSUE:[/yellow] Missing section: ## {section.title()}")
            if section == "usage":
                new_section = _generate_usage_section(meta, body)
            else:
                new_section = f"## {section.title()}\n\nTODO: Add {section} content.\n"

            if dry_run:
                _print(f"  [cyan]WOULD ADD:[/cyan] ## {section.title()} section to SKILL.md")
                _print(f"  [dim]Preview:[/dim]")
                for line in new_section.splitlines()[:8]:
                    _print(f"    {line}")
                if len(new_section.splitlines()) > 8:
                    _print(f"    ... ({len(new_section.splitlines()) - 8} more lines)")
                fixes_preview.append(f"## {section.title()}")
            else:
                # Insert before the first ## section or at the end
                # Find the position after the frontmatter and title
                updated = content.rstrip() + "\n\n" + new_section + "\n"
                skill_md_path.write_text(updated, encoding="utf-8")
                content = updated  # update for subsequent fixes
                _print(f"  [green]FIXED:[/green] Added ## {section.title()} section to SKILL.md")
                fixes_applied.append(f"## {section.title()}")
        else:
            _print(f"  [green]OK:[/green] ## {section.title()} section found")

    # -- Summary --------------------------------------------------------------
    print()
    if dry_run:
        if fixes_preview:
            _print(f"  [bold yellow]DRY RUN:[/bold yellow] {len(fixes_preview)} fix(es) would be applied:")
            for f in fixes_preview:
                _print(f"    → {f}")
            _print("\n  [dim]Run without --dry-run to apply fixes.[/dim]")
        else:
            _print("  [green]No fixes needed — skill looks good![/green]")
        return 0

    if fixes_applied:
        _print(f"  [bold green]Applied {len(fixes_applied)} fix(es):[/bold green]")
        for f in fixes_applied:
            _print(f"    ✔ {f}")

        # Re-validate
        _print("\n  Re-validating ...")
        try:
            result = run_validate(skill_dir)
        except SystemExit as se:
            result = int(str(se.code)) if se.code is not None else 1

        if result == 0:
            _print("\n  [bold green]All fixes applied — validation PASSED! ✔[/bold green]")
            _print("  [dim]Next: run 'zforge publish --dry-run' to preview the full pipeline.[/dim]")
            return 0
        else:
            _print("\n  [yellow]Some issues remain — review output above.[/yellow]")
            return 1
    else:
        _print("  [green]No fixes needed — skill already passes validation! ✔[/green]")
        return 0
