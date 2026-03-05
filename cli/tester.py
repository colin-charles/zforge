"""zforge test -- run SkillTest.md tests."""
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent / "scripts"


def run_test(skill_dir=None) -> int:
    """Run test_runner.py with live streaming output."""
    skill_dir = (Path(skill_dir) if skill_dir else Path.cwd()).resolve()
    script = SCRIPTS_DIR / "test_runner.py"

    if not script.exists():
        print(f"Error: test_runner not found at {script}", file=sys.stderr)
        return 1

    skill_test = skill_dir / "SkillTest.md"
    if not skill_test.exists():
        print(f"Error: no SkillTest.md found in {skill_dir}", file=sys.stderr)
        print("Run 'zforge new' to scaffold or create SkillTest.md manually.", file=sys.stderr)
        return 1

    cmd = [sys.executable, str(script), "--skill", str(skill_dir)]
    print(f"\n  ZeroForge Test -- running tests for '{skill_dir.name}'\n")

    proc = subprocess.Popen(
        cmd, cwd=str(skill_dir),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    for line in iter(proc.stdout.readline, ""):
        print(line, end="", flush=True)
    proc.wait()
    return proc.returncode
