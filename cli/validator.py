"""zforge validate -- self-contained skill directory validator."""
import json
import sys
from pathlib import Path


# ── Required fields in skill.json ────────────────────────────────────────────
REQUIRED_JSON_FIELDS = ["name", "slug", "version", "description", "author", "category", "tags"]

# ── Required SKILL.md section headings (lowercase match) ─────────────────────
REQUIRED_SECTIONS = ["overview", "usage"]


def _header(text: str) -> None:
    width = 60
    print(f"\n{'─' * width}")
    print(f"  ZeroForge Validate — {text}")
    print(f"{'─' * width}\n")


def _ok(msg: str) -> None:
    print(f"  ✅  {msg}")


def _warn(msg: str) -> None:
    print(f"  ⚠️   {msg}")


def _fail(msg: str) -> None:
    print(f"  ❌  {msg}")


def run_validate(skill_dir=None) -> int:
    """Validate a skill directory. Returns 0 on pass, 1 on failure."""
    skill_dir = (Path(skill_dir) if skill_dir else Path.cwd()).resolve()

    _header(f"'{skill_dir.name}'")

    errors   = 0
    warnings = 0

    # ── 1. Directory exists ───────────────────────────────────────────────────
    if not skill_dir.is_dir():
        _fail(f"Directory not found: {skill_dir}")
        print(f"\n  Result: FAIL ({errors+1} error(s))\n")
        return 1
    _ok(f"Directory found: {skill_dir}")

    # ── 2. SKILL.md ───────────────────────────────────────────────────────────
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        _fail("SKILL.md not found")
        errors += 1
    else:
        _ok("SKILL.md exists")
        content_lower = skill_md.read_text(encoding="utf-8", errors="ignore").lower()
        for section in REQUIRED_SECTIONS:
            if f"## {section}" in content_lower:
                _ok(f"  SKILL.md has '## {section.title()}' section")
            else:
                _fail(f"  SKILL.md missing '## {section.title()}' section")
                errors += 1

    # ── 3. skill.json ─────────────────────────────────────────────────────────
    skill_json_path = skill_dir / "skill.json"
    if not skill_json_path.exists():
        _fail("skill.json not found")
        errors += 1
    else:
        _ok("skill.json exists")
        try:
            data = json.loads(skill_json_path.read_text(encoding="utf-8"))
            for field in REQUIRED_JSON_FIELDS:
                val = data.get(field)
                if val is None or val == "" or val == []:
                    _fail(f"  skill.json missing or empty field: '{field}'")
                    errors += 1
                else:
                    _ok(f"  skill.json field '{field}': OK")
        except json.JSONDecodeError as exc:
            _fail(f"  skill.json is not valid JSON: {exc}")
            errors += 1

    # ── 4. Optional but recommended ───────────────────────────────────────────
    if not (skill_dir / "requirements.txt").exists():
        _warn("requirements.txt not found (recommended)")
        warnings += 1
    else:
        _ok("requirements.txt exists")

    if not (skill_dir / "scripts").is_dir():
        _warn("scripts/ directory not found (recommended for runnable skills)")
        warnings += 1
    else:
        _ok("scripts/ directory exists")

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print(f"{'─' * 60}")
    if errors == 0:
        print(f"  ✅  PASS — {warnings} warning(s), 0 error(s)")
        if warnings:
            print("      Skill is valid. Address warnings before publishing.")
        else:
            print("      Skill is valid and ready to publish!")
        print(f"{'─' * 60}\n")
        return 0
    else:
        print(f"  ❌  FAIL — {errors} error(s), {warnings} warning(s)")
        print("      Fix errors above, then re-run: zforge validate")
        print(f"{'─' * 60}\n")
        return 1
