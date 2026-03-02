"""zforge dev -- run the APOL experiment pipeline."""
import subprocess
import sys
from pathlib import Path

# Scripts live inside the cli package (pip-installable)
SCRIPTS_DIR = Path(__file__).parent / "scripts"


def run_dev(
    goal: str = "GOAL.md",
    cycles: int = 3,
    model: str = "openrouter/anthropic/claude-sonnet-4-5",
    skill_dir: Path | None = None,
) -> int:
    """Run 02_run_experiment.py with live streaming output."""
    skill_dir = Path(skill_dir) if skill_dir else Path.cwd()
    goal_path = Path(goal) if Path(goal).is_absolute() else skill_dir / goal
    name = skill_dir.name
    script = SCRIPTS_DIR / "02_run_experiment.py"

    if not script.exists():
        print(f"Error: experiment script not found at {script}", file=sys.stderr)
        print("Try reinstalling: pip install --upgrade zforge", file=sys.stderr)
        return 1

    if not goal_path.exists():
        print(f"Error: GOAL.md not found at {goal_path}", file=sys.stderr)
        print("Create a GOAL.md first or run: zforge new <skill-name>", file=sys.stderr)
        return 1

    cmd = [
        sys.executable, str(script),
        "--goal", str(goal_path),
        "--name", name,
        "--cycles", str(cycles),
        "--model", model,
    ]

    print(f"\n  ZeroForge Dev -- running APOL for '{name}'")
    print(f"   Goal  : {goal_path}")
    print(f"   Cycles: {cycles} | Model: {model}")
    print(f"   Script: {script}\n")

    proc = subprocess.Popen(
        cmd,
        cwd=str(skill_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    for line in iter(proc.stdout.readline, ""):
        print(line, end="", flush=True)

    proc.wait()

    if proc.returncode == 0:
        # Winner lives in <skill_dir>/experiments/NNN_name/WINNER.md
        experiments_dir = skill_dir / "experiments"
        if experiments_dir.exists():
            winners = sorted(experiments_dir.glob("[0-9][0-9][0-9]_*/WINNER.md"))
            if winners:
                print(f"\n  Winner saved to: {winners[-1]}")
    else:
        print(f"\n  Dev run failed with exit code {proc.returncode}", file=sys.stderr)

    return proc.returncode
