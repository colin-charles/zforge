"""zforge dev -- run the APOL experiment pipeline."""
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"


def run_dev(
    goal: str = "GOAL.md",
    cycles: int = 3,
    model: str = "anthropic/claude-sonnet-4-5",
    skill_dir: Path | None = None,
) -> int:
    """Run 02_run_experiment.py with live streaming output."""
    skill_dir = Path(skill_dir) if skill_dir else Path.cwd()
    goal_path = Path(goal) if Path(goal).is_absolute() else skill_dir / goal
    name = skill_dir.name
    script = SCRIPTS_DIR / "02_run_experiment.py"

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
    print(f"   Goal: {goal_path}")
    print(f"   Cycles: {cycles} | Model: {model}\n")

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
        # Experiments live in ZeroForge r-and-d dir, not inside skill dir
        from pathlib import Path as _Path
        _rnd_candidates = [
            skill_dir.parent.parent / "r-and-d" / "experiments",
            _Path("/a0/usr/workdir/ZeroForge/r-and-d/experiments"),
        ]
        _rnd_base = next((p for p in _rnd_candidates if p.exists()), None)
        if _rnd_base:
            _winners = sorted(_rnd_base.glob(f"[0-9][0-9][0-9]_{skill_dir.name}/WINNER.md"))
            if _winners:
                _latest = _winners[-1]
                print(f"\n  Winner saved to: {_latest}")
    else:
        print(f"\n  Dev run failed with exit code {proc.returncode}", file=sys.stderr)

    return proc.returncode
