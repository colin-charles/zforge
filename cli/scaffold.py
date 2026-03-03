"""zforge new — scaffold a new skill directory."""
from pathlib import Path
import shutil
import sys

try:
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

REQUIRED_SECTIONS = [
    "# ",
    "## Overview",
    "## Requirements",
    "## Installation",
    "## Usage",
    "## Examples",
    "## Configuration",
    "## Troubleshooting",
    "## Contributing",
    "## License",
]

SKILL_MD_TEMPLATE = """# SKILL: {name}
**Version:** 0.1.0
**Author:** {author}
**Tags:** TODO: tag1, tag2, tag3
**Category:** TODO: skill|script|template|guide|course|consulting
**License:** MIT

## Description
TODO: 10-100 words describing when an AI agent should use this skill.
Include action verbs, domain nouns, and synonyms so agents know when to invoke it.

## Overview

TODO: Brief description of what this skill does.

## Requirements

- Python 3.10+
- TODO: list dependencies

## Installation

```bash
bash install.sh
```

## Usage

TODO: describe how to use this skill.

## Examples

### Example 1 — Basic

```bash
# TODO: add example command
```

### Example 2 — Advanced

```bash
# TODO: add advanced example
```

### Example 3 — Edge case

```bash
# TODO: add edge case example
```

## Configuration

TODO: describe configuration options.

## Troubleshooting

### Issue: TODO common issue 1
**Fix:** TODO describe fix.

### Issue: TODO common issue 2
**Fix:** TODO describe fix.

## Contributing

Pull requests welcome. Please open an issue first.

## License

MIT
"""

GOAL_MD_TEMPLATE = """# GOAL — {name}

## What this skill should do

TODO: Describe the purpose of this skill in 2-3 sentences.

## Target users

TODO: Who will use this skill? (e.g. developers, analysts, agents)

## Key features

- TODO: feature 1
- TODO: feature 2
- TODO: feature 3

## Success criteria

- [ ] TODO: measurable outcome 1
- [ ] TODO: measurable outcome 2

## Out of scope

- TODO: what this skill should NOT do

## Reference skills / examples

- TODO: link or describe similar skills for inspiration
"""

INSTALL_SH_TEMPLATE = """#!/usr/bin/env bash
set -e
echo "Installing {name} dependencies..."
pip install -r requirements.txt
echo "Installation complete."
"""


def scaffold_skill(name: str, output_dir: Path | None = None, author: str = "") -> Path:
    """Create a new skill directory with all boilerplate files."""
    target = (output_dir or Path.cwd()) / name
    if target.exists():
        _err(f"Directory already exists: {target}")
        sys.exit(1)

    target.mkdir(parents=True)
    (target / "scripts").mkdir()

    # SKILL.md
    (target / "SKILL.md").write_text(SKILL_MD_TEMPLATE.format(name=name, author=author or "your-handle"))

    # GOAL.md
    (target / "GOAL.md").write_text(GOAL_MD_TEMPLATE.format(name=name))

    # install.sh
    install_sh = target / "install.sh"
    install_sh.write_text(INSTALL_SH_TEMPLATE.format(name=name))
    install_sh.chmod(0o755)

    # requirements.txt
    (target / "requirements.txt").write_text("# Add dependencies here\n")

    # Copy SkillTest.md template
    src_test = TEMPLATES_DIR / "SkillTest.md"
    if src_test.exists():
        content = src_test.read_text().replace("[skill_name]", name)
        (target / "SkillTest.md").write_text(content)
    else:
        (target / "SkillTest.md").write_text(f"# SkillTest — {name}\nversion: 1.0\n")

    # Copy skill.json template and populate with correct nested structure
    src_json = TEMPLATES_DIR / "skill.json"
    if src_json.exists():
        import json
        from datetime import datetime
        data = json.loads(src_json.read_text())
        slug = name.replace("_", "-").lower()
        now = datetime.now().strftime("%Y-%m-%d")
        # Update nested metadata keys (NOT flat root keys)
        if "metadata" in data:
            data["metadata"]["name"] = name.replace("_", " ").title()
            data["metadata"]["slug"] = slug
            data["metadata"]["version"] = "0.1.0"
            data["metadata"]["created_at"] = now
            data["metadata"]["updated_at"] = now
            if author:
                data["metadata"]["author"] = author
                data["metadata"]["author_url"] = f"https://github.com/{author}"

        if "description" in data:
            data["description"]["short"] = f"TODO: short description for {name}"
            data["description"]["long"] = f"TODO: long description for {name}"
            data["description"]["description_for_agent"] = f"TODO: when to use {name}"
        if "marketplace" in data:
            data["marketplace"]["listing_url"] = f"https://zero-forge.org/listing/{slug}"
        (target / "skill.json").write_text(json.dumps(data, indent=2))
    else:
        import json
        (target / "skill.json").write_text(json.dumps({"metadata": {"name": name, "version": "0.1.0"}}, indent=2))

    # scripts/main.py placeholder
    (target / "scripts" / "main.py").write_text(
        f"""#!/usr/bin/env python3
# {name} — main entry point
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="{name}")
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if args.version:
        print("{name} v0.1.0")
        sys.exit(0)

    # TODO: implement {name}
    print("{name}: ready.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""
    )

    return target


def _err(msg: str) -> None:
    if HAS_RICH:
        console.print(f"[bold red]Error:[/] {msg}")
    else:
        print(f"Error: {msg}", file=sys.stderr)



def print_success(name: str, target: Path) -> None:
    """Print success panel after scaffolding."""
    steps = (
        "[bold green]Skill scaffolded![/bold green] "
        f"--> [cyan]{target}[/cyan]\n\n"
        "  Next steps:\n"
        "  1. Edit [yellow]GOAL.md[/yellow] -- describe what your skill does\n"
        "  2. Edit [yellow]SKILL.md[/yellow] -- fill in all sections\n"
        "  3. Run [bold]zforge dev[/bold] -- generate with APOL\n"
        f"  4. Run [bold]zforge test --skill {name}/[/bold] -- validate quality"
    )
    if HAS_RICH:
        console.print(Panel(steps, title="[bold magenta]ZeroForge[/]", border_style="magenta"))
    else:
        sep = "=" * 60
        print(f"\n{sep}")
        print(f"Skill scaffolded! --> {target}")
        print(f"Next: edit GOAL.md then run zforge dev")
        print(f"{sep}\n")
