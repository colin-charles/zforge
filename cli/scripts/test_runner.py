#!/usr/bin/env python3
"""
test_runner.py -- ZeroForge skill test harness.

Runs structural and basic runtime tests on a skill directory.
Usage: python test_runner.py --skill <path-to-skill-dir>
"""
import argparse
import json
import sys
from pathlib import Path

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"


def check(label: str, condition: bool, warn_only: bool = False) -> bool:
    tag = PASS if condition else (WARN if warn_only else FAIL)
    print(f"  {tag}  {label}")
    return condition


def run_tests(skill_dir: Path) -> int:
    """Run all tests. Returns 0 on pass, 1 on failure."""
    print(f"\n  ZeroForge Test Runner -- '{skill_dir.name}'")
    print(f"  Path: {skill_dir}\n")

    failures = 0

    # --- Structural tests ---
    print("  -- Structure --")
    has_skill_md = check("SKILL.md exists", (skill_dir / "SKILL.md").exists())
    has_skill_json = check("skill.json exists", (skill_dir / "skill.json").exists())
    check("README.md exists", (skill_dir / "README.md").exists(), warn_only=True)

    if not has_skill_md:
        failures += 1
    if not has_skill_json:
        failures += 1

    # --- SKILL.md content tests ---
    print("\n  -- SKILL.md --")
    if has_skill_md:
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        word_count = len(content.split())
        if not check("SKILL.md >= 200 words", word_count >= 200):
            failures += 1
        check("Has ## Usage section", "## Usage" in content or "## How" in content, warn_only=True)
        check("Has ## Examples section", "## Example" in content, warn_only=True)
        print(f"         Word count: {word_count}")

    # --- skill.json content tests ---
    print("\n  -- skill.json --")
    if has_skill_json:
        try:
            data = json.loads((skill_dir / "skill.json").read_text(encoding="utf-8"))
            meta = data.get("metadata", {})
            desc = data.get("description", {})
            quality = data.get("quality", {})

            # Required metadata fields (nested under 'metadata')
            required_meta = ["name", "version", "author", "tags"]
            for field in required_meta:
                if not check(f"metadata.{field} present", bool(meta.get(field))):
                    failures += 1

            # Description fields (nested under 'description')
            if not check("description.short present", bool(desc.get("short"))):
                failures += 1

            # Quality fields (warn only — populated after APOL cert)
            check("quality.apol_certified field present", "apol_certified" in quality, warn_only=True)
            if quality.get("apol_certified"):
                check("quality.apol_composite_score present", bool(quality.get("apol_composite_score")), warn_only=True)
        except json.JSONDecodeError as e:
            print(f"  {FAIL}  skill.json is invalid JSON: {e}")
            failures += 1

    # --- Scripts tests ---
    scripts_dir = skill_dir / "scripts"
    print("\n  -- Scripts --")
    if scripts_dir.exists():
        scripts = list(scripts_dir.glob("*.py")) + list(scripts_dir.glob("*.sh"))
        check(f"scripts/ has {len(scripts)} file(s)", len(scripts) > 0, warn_only=True)
        for s in scripts:
            check(f"Script readable: {s.name}", s.stat().st_size > 0, warn_only=True)
    else:
        check("scripts/ directory exists", False, warn_only=True)

    # --- Summary ---
    print()
    if failures == 0:
        print("  ✓ All tests passed")
    else:
        print(f"  ✗ {failures} test(s) failed")

    return 0 if failures == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="ZeroForge skill test runner")
    parser.add_argument("--skill", required=True, help="Path to skill directory")
    args = parser.parse_args()

    skill_dir = Path(args.skill).resolve()
    if not skill_dir.is_dir():
        print(f"Error: not a directory: {skill_dir}", file=sys.stderr)
        sys.exit(1)

    sys.exit(run_tests(skill_dir))


if __name__ == "__main__":
    main()
