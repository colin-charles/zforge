#!/usr/bin/env python3
"""
ZeroForge Release Automation
Usage: python scripts/release.py <version> "<summary>" [--fix|--feature|--changed|--meta|--launch]

Examples:
  python scripts/release.py 2.1.36 "Fixed upgrade loop on fresh install" --fix
  python scripts/release.py 2.2.0 "Added zforge search command" --feature

The website changelog reads CHANGELOG.md directly from GitHub at runtime,
so only the zforge repo needs updating here.
"""

import sys
import os
import re
import subprocess
from datetime import date
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────
ZFORGE_REPO  = Path(__file__).parent.parent
PYPROJECT    = ZFORGE_REPO / "pyproject.toml"
CHANGELOG_MD = ZFORGE_REPO / "CHANGELOG.md"

TAG_MAP = {
    "--fix":     "FIX",
    "--feature": "FEATURE",
    "--changed": "CHANGED",
    "--meta":    "META",
    "--launch":  "LAUNCH",
}

SECTION_MAP = {
    "FIX":     "Fixed",
    "FEATURE": "Added",
    "CHANGED": "Changed",
    "META":    "Changed",
    "LAUNCH":  "Added",
}

# ── Helpers ──────────────────────────────────────────────────────────────────
def run(cmd, cwd=None):
    print("  $ " + cmd)
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    if result.returncode != 0:
        print("\n❌ Command failed: " + cmd)
        sys.exit(1)
    return result

def bump_version(new_ver):
    content = PYPROJECT.read_text()
    match = re.search(r'version = "([0-9.]+)"', content)
    if not match:
        print("❌ Could not find version in pyproject.toml")
        sys.exit(1)
    old_ver = match.group(1)
    content = content.replace('version = "' + old_ver + '"', 'version = "' + new_ver + '"' )
    PYPROJECT.write_text(content)
    # Bump __version__ in cli/__init__.py if present
    init_file = ZFORGE_REPO / "cli/__init__.py"
    if init_file.exists():
        ic = init_file.read_text()
        ic = re.sub(r'__version__\s*=\s*"[0-9.]+"', '__version__ = "' + new_ver + '"', ic)
        init_file.write_text(ic)
    print("  ✅ Version bumped: " + old_ver + " → " + new_ver)
    return old_ver

def update_changelog_md(version, summary, tag_name, today):
    section = SECTION_MAP.get(tag_name, "Changed")
    entry = "## [" + version + "] - " + today + "\n### " + section + "\n- " + summary + "\n\n"
    content = CHANGELOG_MD.read_text()
    lines = content.split("\n")
    insert_at = 1
    for i, line in enumerate(lines):
        if line.startswith("## ["):
            insert_at = i
            break
    lines.insert(insert_at, entry)
    CHANGELOG_MD.write_text("\n".join(lines))
    print("  ✅ CHANGELOG.md updated")

def build_and_publish():
    dist = ZFORGE_REPO / "dist"
    run("rm -rf " + str(dist), cwd=ZFORGE_REPO)
    run("python -m build", cwd=ZFORGE_REPO)
    pypi_token = os.environ.get("PYPI_TOKEN", "")
    if not pypi_token:
        print("  ⚠️  PYPI_TOKEN not set — skipping PyPI upload")
        return
    run("python -m twine upload dist/* --username __token__ --password " + pypi_token, cwd=ZFORGE_REPO)
    print("  ✅ Published to PyPI")

def git_push_zforge(version):
    run("git add -A", cwd=ZFORGE_REPO)
    run("git commit -m 'release: v" + version + "'", cwd=ZFORGE_REPO)
    run("git tag v" + version, cwd=ZFORGE_REPO)
    run("git push origin main", cwd=ZFORGE_REPO)
    run("git push origin v" + version, cwd=ZFORGE_REPO)
    print("  ✅ zforge repo pushed + tagged")

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    version  = sys.argv[1]
    summary  = sys.argv[2]
    flag     = sys.argv[3] if len(sys.argv) > 3 else "--fix"
    today    = date.today().isoformat()

    if flag not in TAG_MAP:
        print("Unknown flag: " + flag + ". Use one of: " + str(list(TAG_MAP.keys())))
        sys.exit(1)

    tag_name = TAG_MAP[flag]

    print("")
    print("🚀 Releasing zforge v" + version + " [" + tag_name + "]")
    print("   Summary : " + summary)
    print("   Date    : " + today)
    print("")

    print("[1/4] Bumping version...")
    bump_version(version)

    print("[2/4] Updating CHANGELOG.md...")
    update_changelog_md(version, summary, tag_name, today)

    print("[3/4] Building & publishing to PyPI...")
    build_and_publish()

    print("[4/4] Pushing zforge repo + tag...")
    git_push_zforge(version)

    print("")
    print("✅ zforge v" + version + " released!")
    print("   PyPI      : https://pypi.org/project/zforge/" + version + "/")
    print("   Changelog : https://zero-forge.org/changelog/")
    print("   Upgrade   : pip install --upgrade zforge")
    print("")
    print("   ℹ️  Website changelog auto-reads from GitHub — no separate push needed.")

if __name__ == "__main__":
    main()
