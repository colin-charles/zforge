#!/usr/bin/env python3
"""
test_runner.py -- ZeroForge skill test harness.

Runs structural, metadata, syntax, and runtime smoke tests on a skill directory.
Usage: python test_runner.py --skill <path-to-skill-dir>
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"
SKIP = "[SKIP]"


def check(label: str, condition: bool, warn_only: bool = False) -> bool:
    tag = PASS if condition else (WARN if warn_only else FAIL)
    print(f"  {tag}  {label}")
    return condition


def _unquote(s: str) -> str:
    """Strip matching surrounding quotes only (prevents stripping embedded quotes)."""
    if len(s) >= 2 and s[0] in ("'", '"') and s[-1] == s[0]:
        return s[1:-1]
    return s


def _run_cmd(cmd: list, cwd: Path, timeout: int = 30) -> tuple:
    """Run a command, return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, cwd=str(cwd),
            capture_output=True, text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"TIMEOUT after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


def parse_skilltest(skill_dir: Path) -> list:
    """
    Parse SkillTest.md for test blocks.
    Each block starts with a heading and contains key:value pairs + a command.
    Returns list of dicts with keys: name, command, expect_exit, expect_output.
    """
    skilltest_path = skill_dir / "SkillTest.md"
    if not skilltest_path.exists():
        return []

    tests = []
    content = skilltest_path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^#{2,3}\s+", content)
    for block in blocks[1:]:
        lines = block.strip().splitlines()
        if not lines:
            continue
        test_name = lines[0].strip()
        test = {"name": test_name, "command": None, "expect_exit": 0, "expect_output": None}
        for line in lines[1:]:
            m = re.match(r"^[-*]?\s*(\w+)\s*:\s*(.+)$", line.strip())
            if m:
                key = m.group(1).lower()
                raw_val = _unquote(m.group(2).strip())
                if key == "command":
                    test["command"] = raw_val
                elif key in ("expect_exit", "exit"):
                    try:
                        test["expect_exit"] = int(raw_val)
                    except ValueError:
                        pass
                elif key in ("expect_output", "output"):
                    test["expect_output"] = raw_val
        if test["command"]:
            tests.append(test)
    return tests


def run_tests(skill_dir: Path) -> int:
    """Run all tests. Returns 0 on pass, 1 on failure."""
    skill_name = skill_dir.name
    print(f"\n  ZeroForge Test Runner -- {skill_name}")
    print(f"  Path: {skill_dir}\n")
    failures = 0

    # ── Structure ─────────────────────────────────────────────────
    print("  -- Structure --")
    has_skill_md   = check("SKILL.md exists",   (skill_dir / "SKILL.md").exists())
    has_skill_json = check("skill.json exists", (skill_dir / "skill.json").exists())
    check("README.md exists", (skill_dir / "README.md").exists(), warn_only=True)
    if not has_skill_md:
        failures += 1
    if not has_skill_json:
        failures += 1

    # ── SKILL.md content ──────────────────────────────────────────
    print("\n  -- SKILL.md --")
    if has_skill_md:
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        word_count = len(content.split())
        if not check("SKILL.md >= 200 words", word_count >= 200):
            failures += 1
        check("Has ## Usage section",    "## Usage" in content or "## How" in content, warn_only=True)
        check("Has ## Examples section", "## Example" in content, warn_only=True)
        print(f"         Word count: {word_count}")

    # ── skill.json metadata ───────────────────────────────────────
    print("\n  -- skill.json --")
    if has_skill_json:
        try:
            data    = json.loads((skill_dir / "skill.json").read_text(encoding="utf-8"))
            meta    = data.get("metadata", {})
            desc    = data.get("description", {})
            quality = data.get("quality", {})
            for field in ["name", "version", "author", "tags"]:
                if not check(f"metadata.{field} present", bool(meta.get(field))):
                    failures += 1
            if not check("description.short present", bool(desc.get("short"))):
                failures += 1
            check("quality.apol_certified field present", "apol_certified" in quality, warn_only=True)
            if quality.get("apol_certified"):
                check("quality.apol_composite_score present", bool(quality.get("apol_composite_score")), warn_only=True)
        except json.JSONDecodeError as e:
            print(f"  {FAIL}  skill.json is invalid JSON: {e}")
            failures += 1

    # ── Scripts: existence ────────────────────────────────────────
    scripts_dir = skill_dir / "scripts"
    print("\n  -- Scripts --")
    py_scripts = []
    if scripts_dir.exists():
        py_scripts  = list(scripts_dir.glob("*.py"))
        sh_scripts  = list(scripts_dir.glob("*.sh"))
        all_scripts = py_scripts + sh_scripts
        check(f"scripts/ has {len(all_scripts)} file(s)", len(all_scripts) > 0, warn_only=True)
        for s in all_scripts:
            check(f"Script readable: {s.name}", s.stat().st_size > 0, warn_only=True)
    else:
        check("scripts/ directory exists", False, warn_only=True)

    # ── Syntax check: all .py scripts ────────────────────────────
    print("\n  -- Syntax Check --")
    if py_scripts:
        for script in py_scripts:
            rc, _, stderr = _run_cmd(
                [sys.executable, "-m", "py_compile", str(script)],
                cwd=skill_dir
            )
            passed = (rc == 0)
            if not check(f"Syntax OK: {script.name}", passed):
                failures += 1
                if stderr:
                    for line in stderr.strip().splitlines()[:3]:
                        print(f"         {line}")
    else:
        print(f"  {SKIP}  No Python scripts found to syntax-check")

    # ── Runtime smoke test: scripts/main.py ──────────────────────
    print("\n  -- Runtime Smoke Test --")
    main_script = (scripts_dir / "main.py") if scripts_dir.exists() else None
    if main_script and main_script.exists():
        rc, stdout, stderr = _run_cmd(
            [sys.executable, str(main_script), "--help"],
            cwd=skill_dir, timeout=30
        )
        if rc == 0:
            check("scripts/main.py --help exits cleanly (exit 0)", True)
        elif rc == 2:
            check("scripts/main.py loads OK (exit 2 = args required)", True)
        elif rc == -1 and "TIMEOUT" in stderr:
            if not check("scripts/main.py --help timed out after 30s", False):
                failures += 1
        else:
            rc2, stdout2, stderr2 = _run_cmd(
                [sys.executable, str(main_script)],
                cwd=skill_dir, timeout=30
            )
            if rc2 in (0, 2):
                check("scripts/main.py runs without crash", True)
            else:
                if not check("scripts/main.py runs without error", False):
                    failures += 1
                combined = (stderr or stderr2 or stdout or stdout2).strip()
                for line in combined.splitlines()[:5]:
                    print(f"         {line}")
    else:
        print(f"  {SKIP}  No scripts/main.py found -- skipping smoke test")

    # ── SkillTest.md custom tests ─────────────────────────────────
    print("\n  -- SkillTest.md --")
    custom_tests = parse_skilltest(skill_dir)
    if custom_tests:
        print(f"  Found {len(custom_tests)} custom test(s)")
        for t in custom_tests:
            cmd_str   = t["command"]
            expect_rc = t["expect_exit"]
            label     = t["name"]
            cmd_parts = cmd_str.split()
            if cmd_parts and (skill_dir / cmd_parts[0]).exists():
                cmd_parts[0] = str(skill_dir / cmd_parts[0])
            rc, stdout, stderr = _run_cmd(cmd_parts, cwd=skill_dir, timeout=60)
            passed = (rc == expect_rc)
            if not check(f"Custom test: {label} (exit {rc}, expected {expect_rc})", passed):
                failures += 1
                combined = (stderr or stdout).strip()
                for line in combined.splitlines()[:3]:
                    print(f"         {line}")
            elif t["expect_output"] and t["expect_output"] not in stdout:
                exp = t["expect_output"][:40]
                if not check(f"  Output contains: {exp}", False):
                    failures += 1
    else:
        print(f"  {SKIP}  No custom tests in SkillTest.md")
        print("         Tip: add ## Test Name / command: python scripts/main.py blocks")

    # ── Summary ───────────────────────────────────────────────────
    print()
    if failures == 0:
        print("  ✓ All tests passed")
    else:
        print(f"  ✗ {failures} test(s) failed")
    return 0 if failures == 0 else 1


def main() -> None:
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
