"""ZeroForge skill validator — checks SKILL.md and skill.json compliance."""
from pathlib import Path
import json
import re

from cli._constants import VALID_CATEGORIES

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_TAGS = {
    "agent": "skill", "automation": "skill", "productivity": "skill",
    "ai": "skill", "security": "skill", "media": "skill", "utility": "skill",
}
REQUIRED_SECTIONS = ["overview", "usage"]

LINE = chr(9472) * 60

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _header(text: str) -> None:
    print("\n" + LINE)
    print("  ZeroForge Validate -- " + text)
    print(LINE + "\n")

def _ok(msg: str)   -> None: print("  [OK]   " + msg)
def _warn(msg: str) -> None: print("  [WARN] " + msg)
def _fail(msg: str) -> None: print("  [FAIL] " + msg)

# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def run_validate(skill_dir=None) -> int:
    """Validate a skill directory. Returns 0 on pass, 1 on failure."""
    skill_dir = (Path(skill_dir) if skill_dir else Path.cwd()).resolve()

    _header("'" + skill_dir.name + "'")

    errors   = 0
    warnings = 0

    # -- 1. Directory exists --------------------------------------------------
    if not skill_dir.is_dir():
        _fail("Directory not found: " + str(skill_dir))
        print("\n  Result: FAIL (1 error)\n")
        return 1
    _ok("Directory found: " + str(skill_dir))

    # -- 2. SKILL.md ----------------------------------------------------------
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        _fail("SKILL.md not found")
        errors += 1
    else:
        _ok("SKILL.md exists")
        content = skill_md.read_text(encoding="utf-8", errors="replace").lower()
        for section in REQUIRED_SECTIONS:
            pattern = r"^#{1,3}\s+" + re.escape(section)
            if re.search(pattern, content, re.MULTILINE):
                _ok("Section found: " + section)
            else:
                _fail("Missing required section: " + section)
                errors += 1

    # -- 3. skill.json --------------------------------------------------------
    skill_json_path = skill_dir / "skill.json"
    if not skill_json_path.exists():
        _fail("skill.json not found")
        errors += 1
    else:
        _ok("skill.json exists")
        try:
            data = json.loads(skill_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            _fail("skill.json is not valid JSON: " + str(exc))
            errors += 1
            data = {}

        if data:
            meta = data.get("metadata", data)  # support flat or nested

            # Required fields
            for field in ("name", "version", "description", "author", "category"):
                val = meta.get(field, data.get(field, ""))
                if not val:
                    _fail("Missing required field: " + field)
                    errors += 1
                else:
                    _ok("Field present: " + field)

            # Category validation
            cat = meta.get("category", data.get("category", ""))
            if cat and cat not in VALID_CATEGORIES:
                _fail("Invalid category '" + cat + "'. Must be one of: " + ", ".join(sorted(VALID_CATEGORIES)))
                errors += 1

            # Description length check
            desc = meta.get("description", data.get("description", ""))
            if isinstance(desc, dict):
                short = desc.get("short", "")
                long_ = desc.get("long", "")
                if short and len(short) > 120:
                    _fail("description.short is " + str(len(short)) + " chars -- must be <=120")
                    _fail("  Current: '" + short[:60] + "...'")
                    errors += 1
                elif short:
                    _ok("description.short length OK (" + str(len(short)) + " chars)")
                if long_ and len(long_) < 20:
                    _warn("description.long seems very short (" + str(len(long_)) + " chars)")
                    warnings += 1
            elif isinstance(desc, str):
                if len(desc) > 300:
                    _warn("description is " + str(len(desc)) + " chars -- consider keeping under 300")
                    warnings += 1

    # -- 4. Result ------------------------------------------------------------
    print("\n" + LINE)
    if errors == 0:
        _ok("PASS  " + str(warnings) + " warning(s), 0 error(s)")
        print(LINE + "\n")
        return 0
    else:
        _fail("FAIL  " + str(errors) + " error(s), " + str(warnings) + " warning(s)")
        print(LINE + "\n")
        return 1
