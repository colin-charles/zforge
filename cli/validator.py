"""
zforge validate -- self-contained skill directory validator.
Mirrors publisher.py constraints so validate catches all errors before publish.
"""
import json
import sys
from pathlib import Path


# ── Required fields under skill.json["metadata"] ─────────────────────────────
REQUIRED_METADATA_FIELDS = ["name", "slug", "version", "author", "category", "tags"]

# ── Required fields under skill.json["description"] ──────────────────────────
REQUIRED_DESCRIPTION_FIELDS = ["short", "description_for_agent"]

# ── Valid categories (post-mapping) ──────────────────────────────────────────
CATEGORY_MAP = {
    "dev-tools": "skill", "development": "skill", "tool": "skill",
    "guide": "guide", "tutorial": "guide", "howto": "guide",
    "template": "template", "scaffold": "template",
    "script": "script", "automation": "script",
    "course": "course", "training": "course",
    "consulting": "consulting", "service": "consulting",
    "productivity": "skill", "data": "skill", "web": "skill",
    "ai": "skill", "security": "skill", "media": "skill", "utility": "skill",
}
VALID_CATEGORIES = {"skill", "guide", "template", "script", "course", "consulting"}

# ── Required SKILL.md section headings (lowercase) ───────────────────────────
REQUIRED_SECTIONS = ["overview", "usage"]


def _header(text: str) -> None:
    width = 60
    print(f"
{chr(9472) * width}")
    print(f"  ZeroForge Validate — {text}")
    print(f"{chr(9472) * width}
")


def _ok(msg: str) -> None:   print(f"  ✅  {msg}")
def _warn(msg: str) -> None: print(f"  ⚠️   {msg}")
def _fail(msg: str) -> None: print(f"  ❌  {msg}")


def run_validate(skill_dir=None) -> int:
    """Validate a skill directory. Returns 0 on pass, 1 on failure."""
    skill_dir = (Path(skill_dir) if skill_dir else Path.cwd()).resolve()

    _header(f"'{skill_dir.name}' ")

    errors   = 0
    warnings = 0

    # ── 1. Directory exists ───────────────────────────────────────────────────
    if not skill_dir.is_dir():
        _fail(f"Directory not found: {skill_dir}")
        print(f"
  Result: FAIL (1 error)
")
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
                _ok(f"  SKILL.md section '## {section.title()}': found")
            else:
                _fail(f"  SKILL.md missing '## {section.title()}' section")
                errors += 1

    # ── 3. skill.json — structure & constraints ───────────────────────────────
    skill_json_path = skill_dir / "skill.json"
    if not skill_json_path.exists():
        _fail("skill.json not found")
        errors += 1
    else:
        _ok("skill.json exists")
        try:
            data = json.loads(skill_json_path.read_text(encoding="utf-8"))

            # 3a. metadata block
            meta = data.get("metadata", {})
            if not isinstance(meta, dict) or not meta:
                _fail("  skill.json missing 'metadata' block")
                errors += 1
            else:
                _ok("  metadata block found")
                for field in REQUIRED_METADATA_FIELDS:
                    val = meta.get(field)
                    if val is None or val == "" or val == []:
                        _fail(f"  metadata.{field}: missing or empty")
                        errors += 1
                    else:
                        _ok(f"  metadata.{field}: OK")

                # category validity check
                raw_cat = (meta.get("category") or "").lower().strip()
                mapped = CATEGORY_MAP.get(raw_cat, raw_cat)
                if mapped not in VALID_CATEGORIES:
                    _fail(f"  metadata.category '{raw_cat}' is not a recognised category")
                    _fail(f"      Valid: {sorted(VALID_CATEGORIES)}")
                    errors += 1
                else:
                    _ok(f"  metadata.category maps to '{mapped}': OK")

            # 3b. description block
            desc = data.get("description", {})
            if not isinstance(desc, dict) or not desc:
                _fail("  skill.json missing 'description' block")
                errors += 1
            else:
                _ok("  description block found")

                # short description — required + <=120 chars
                short = desc.get("short", "")
                if not short:
                    _fail("  description.short: missing or empty")
                    errors += 1
                elif len(short) > 120:
                    _fail(f"  description.short: {len(short)} chars — must be <=120")
                    _fail(f"      Current: "{short[:60]}..."")
                    errors += 1
                else:
                    _ok(f"  description.short: {len(short)} chars (<=120) OK")

                # long description — recommended
                long_desc = desc.get("long", "")
                if not long_desc:
                    _warn("  description.long: missing (recommended)")
                    warnings += 1
                else:
                    _ok("  description.long: OK")

                # description_for_agent — required + >=10 words
                agent_desc = desc.get("description_for_agent", "")
                if not agent_desc:
                    _fail("  description.description_for_agent: missing or empty")
                    errors += 1
                else:
                    word_count = len(agent_desc.split())
                    if word_count < 10:
                        _fail(f"  description.description_for_agent: {word_count} words — must be >=10")
                        errors += 1
                    else:
                        _ok(f"  description.description_for_agent: {word_count} words (>=10) OK")

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
    print(chr(9472) * 60)
    if errors == 0:
        print(f"  ✅  PASS — {warnings} warning(s), 0 error(s)")
        if warnings:
            print("      Skill is valid. Address warnings before publishing.")
        else:
            print("      Skill is valid and ready to publish!")
        print(chr(9472) * 60 + "
")
        return 0
    else:
        print(f"  ❌  FAIL — {errors} error(s), {warnings} warning(s)")
        print("      Fix errors above, then re-run: zforge validate")
        print(chr(9472) * 60 + "
")
        return 1
