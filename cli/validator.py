"""zforge validate -- validate a skill directory."""
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"


def run_validate(skill_dir=None):
    """Run 04_validate_skill.py with live streaming output."""
    skill_dir = (Path(skill_dir) if skill_dir else Path.cwd()).resolve()
    script = SCRIPTS_DIR / "04_validate_skill.py"

    if not script.exists():
        print(f"Error: validate script not found at {script}", file=sys.stderr)
        return 1

    cmd = [sys.executable, str(script), "--skill", str(skill_dir)]
    print(f"\n  ZeroForge Validate -- checking '{skill_dir.name}'\n")

    proc = subprocess.Popen(
        cmd, cwd=str(skill_dir),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    for line in iter(proc.stdout.readline, ""):
        print(line, end="", flush=True)
    proc.wait()
    return proc.returncode
