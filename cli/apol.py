"""
cli/apol.py  —  APOL (Agent-Oriented Proficiency Level) certification pipeline.

Flow:
  1. Score SKILL.md via apol-judge edge function
  2. If score >= THRESHOLD  →  CERTIFIED immediately (no content changes)
  3. If score <  THRESHOLD  →  prompt creator:
       A) Publish as-is (UNCERTIFIED)
       B) Run APOL refinement pipeline to earn CERTIFIED
  4. Option B: apol-refine edge function improves documentation quality
     - creator intent is locked (never changed)
     - creator sees diff and must confirm before SKILL.md is overwritten
     - up to MAX_CYCLES attempts

Returns:
  ApolResult dataclass with .certified bool, .score float, .skill_md str
"""
from __future__ import annotations

import os
import sys
import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from cli._console import HAS_RICH, console, _print, _rule
from cli._constants import (
    CERTIFIED_THRESHOLD, _CLI_TOKEN, _PUBLIC_SUPABASE_URL,
)

try:
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    from rich.syntax import Syntax
except ImportError:
    pass

# ── Constants ────────────────────────────────────────────────────────────────
MAX_CYCLES          = 3


# ── Helpers ──────────────────────────────────────────────────────────────────

_rprint = _print  # alias for backward compat


# _rule imported from cli._console


def _ask(prompt: str) -> str:
    """Read a single character choice from stdin (works in TTY and piped)."""
    try:
        return input(prompt).strip().upper()
    except (EOFError, KeyboardInterrupt):
        return "A"  # safe default — never auto-modify creator content


def _supabase_url() -> str:
    return (os.environ.get("SUPABASE_URL") or _PUBLIC_SUPABASE_URL).rstrip("/")


def _judge_url() -> str:
    return f"{_supabase_url()}/functions/v1/apol-judge"


def _refine_url() -> str:
    return f"{_supabase_url()}/functions/v1/apol-refine"


# ── Result type ──────────────────────────────────────────────────────────────

@dataclass
class ApolResult:
    certified:    bool
    score:        float
    skill_md:     str          # final SKILL.md content (may be improved if creator accepted)
    cert_id:      Optional[str]  = None
    kpi_scores:   dict           = field(default_factory=dict)
    cycles_run:   int            = 0
    skipped:      bool           = False   # True when edge functions unavailable


# ── Core functions ───────────────────────────────────────────────────────────

def _call_judge(skill_md: str) -> dict:
    """Call apol-judge edge function. Returns parsed JSON response."""
    if not HAS_REQUESTS:
        raise RuntimeError("pip install requests")
    resp = requests.post(
        _judge_url(),
        headers={"Content-Type": "application/json", "x-zforge-token": _CLI_TOKEN},
        json={"skill_md": skill_md},
        timeout=90,
    )
    if resp.status_code == 200:
        return resp.json()
    raise RuntimeError(f"apol-judge [{resp.status_code}]: {resp.text[:300]}")


def _call_refine(skill_md: str, feedback: dict, summary: str) -> str:
    """Call apol-refine edge function. Returns improved SKILL.md string."""
    if not HAS_REQUESTS:
        raise RuntimeError("pip install requests")
    resp = requests.post(
        _refine_url(),
        headers={"Content-Type": "application/json", "x-zforge-token": _CLI_TOKEN},
        json={"skill_md": skill_md, "feedback": feedback, "summary": summary},
        timeout=60,
    )
    if resp.status_code == 200:
        data = resp.json()
        improved = data.get("improved_skill_md", "").strip()
        if not improved:
            raise RuntimeError("apol-refine returned empty content")
        return improved
    raise RuntimeError(f"apol-refine [{resp.status_code}]: {resp.text[:300]}")


def _show_score(score: float, kpis: dict, summary: str, cycle: int = 0) -> None:
    """Pretty-print the APOL judge result."""
    label = "CERTIFIED ✅" if score >= CERTIFIED_THRESHOLD else "Below threshold ❌"
    cycle_str = f"  (cycle {cycle})" if cycle > 0 else ""

    if HAS_RICH:
        t = Table(box=box.SIMPLE, show_header=False)
        t.add_column("KPI", style="dim")
        t.add_column("Score", style="bold")
        t.add_column("Note")
        for kpi_key, kpi_data in kpis.items():
            s = kpi_data.get("score", 0)
            note = kpi_data.get("feedback", "")
            if kpi_key == "kpi5":
                colour = "green" if s == 1 else "red"
                kpi5_label = "✅ READY" if s == 1 else "❌ NOT READY"
                t.add_row(kpi_key.upper(), f"[{colour}]{kpi5_label}[/{colour}]", note)
            else:
                colour = "green" if s >= 4 else ("yellow" if s >= 3 else "red")
                t.add_row(kpi_key.upper(), f"[{colour}]{s}/5[/{colour}]", note)
        score_colour = "green" if score >= CERTIFIED_THRESHOLD else "yellow"
        title = f"[bold {score_colour}]APOL Score: {score:.2f} / 1.00  —  {label}{cycle_str}[/bold {score_colour}]"
        console.print(Panel(t, title=title, subtitle=f"[dim]{summary}[/dim]", border_style=score_colour))
    else:
        print(f"\n  APOL Score: {score:.2f} / 1.00  —  {label}{cycle_str}")
        for kpi_key, kpi_data in kpis.items():
            s = kpi_data.get('score', 0)
            fb = kpi_data.get('feedback', '')
            if kpi_key == "kpi5":
                kpi5_label = "✅ READY" if s == 1 else "❌ NOT READY"
                print(f"    {kpi_key.upper()}: {kpi5_label}  — {fb}")
            else:
                print(f"    {kpi_key.upper()}: {s}/5  — {fb}")
        print(f"  Summary: {summary}")


def _show_diff(original: str, improved: str) -> None:
    """Show a unified diff of the two SKILL.md versions."""
    orig_lines = original.splitlines(keepends=True)
    impr_lines = improved.splitlines(keepends=True)
    diff = list(difflib.unified_diff(
        orig_lines, impr_lines,
        fromfile="SKILL.md (original)",
        tofile="SKILL.md (improved)",
        n=3,
    ))
    if not diff:
        _rprint("  [dim]No content changes detected.[/dim]")
        return
    if HAS_RICH:
        diff_text = "".join(diff[:120])  # cap at 120 lines for readability
        if len(diff) > 120:
            diff_text += f"\n... ({len(diff)-120} more lines) ..."
        console.print(Syntax(diff_text, "diff", theme="monokai", line_numbers=False))
    else:
        for line in diff[:120]:
            print(line, end="")
        if len(diff) > 120:
            print(f"\n... ({len(diff)-120} more lines) ...")


# ── Main entry point ─────────────────────────────────────────────────────────

def apol_certify(skill_dir: Path) -> ApolResult:
    """
    Run the full APOL certification flow for the skill at skill_dir.
    Returns ApolResult — caller decides whether to proceed with publish.
    """
    skill_md_path = skill_dir / "SKILL.md"
    if not skill_md_path.exists():
        _rprint(f"  [yellow]SKILL.md not found — skipping APOL scoring[/yellow]")
        return ApolResult(certified=False, score=0.0, skill_md="", skipped=True)

    original_skill_md = skill_md_path.read_text(encoding="utf-8")
    current_skill_md  = original_skill_md

    _rule("APOL Certification")
    _rprint("  Scoring your SKILL.md with APOL judge ...")

    # ── Phase 1: Score as-is ─────────────────────────────────────────────────
    try:
        result = _call_judge(current_skill_md)
    except Exception as e:
        _rprint(f"  [yellow]APOL judge unavailable ({e}) — skipping APOL scoring[/yellow]")
        return ApolResult(certified=False, score=0.0, skill_md=current_skill_md, skipped=True)

    score    = float(result.get("composite", 0.0))
    _fb      = result.get("feedback", {})
    kpis     = {
        "kpi2": {"score": result.get("kpi2", 1), "feedback": _fb.get("kpi2", "")},
        "kpi3": {"score": result.get("kpi3", 1), "feedback": _fb.get("kpi3", "")},
        "kpi4": {"score": result.get("kpi4", 1), "feedback": _fb.get("kpi4", "")},
        "kpi5": {"score": result.get("kpi5", 0), "feedback": _fb.get("kpi5", "")},
    }
    summary  = result.get("summary", "")
    feedback = _fb
    cert_id  = result.get("cert_id", None)

    _show_score(score, kpis, summary)

    # ── Already CERTIFIED ────────────────────────────────────────────────────
    if score >= CERTIFIED_THRESHOLD:
        _rprint(f"  [bold green]CERTIFIED! Score {score:.2f} meets threshold {CERTIFIED_THRESHOLD:.2f}[/bold green]")
        return ApolResult(
            certified=True,
            score=score,
            skill_md=current_skill_md,
            cert_id=cert_id,
            kpi_scores=kpis,
        )

    # ── Below threshold — A/B decision ───────────────────────────────────────
    _rprint(f"\n  [yellow]Score {score:.2f} is below the CERTIFIED threshold of {CERTIFIED_THRESHOLD:.2f}[/yellow]\n")

    if HAS_RICH:
        console.print(Panel(
            "[bold]A)[/bold]  Publish now as [yellow]UNCERTIFIED[/yellow]\n"
            "[bold]B)[/bold]  Run APOL pipeline to improve and earn [green]CERTIFIED[/green]\n\n"
            "[dim]Option B preserves your skill's intent — only documentation quality is improved.[/dim]\n"
            "[dim]You will review and approve any changes before they are saved.[/dim]",
            title="[bold cyan]What would you like to do?[/bold cyan]",
            border_style="cyan",
        ))
    else:
        print("\n  A) Publish now as UNCERTIFIED")
        print("  B) Run APOL pipeline to improve and earn CERTIFIED")
        print("     (Your skill's intent will never be changed — you review all edits)\n")

    choice = _ask("  Your choice [A/B]: ")

    if choice != "B":
        _rprint("  [dim]Publishing as UNCERTIFIED.[/dim]")
        return ApolResult(
            certified=False,
            score=score,
            skill_md=current_skill_md,
            kpi_scores=kpis,
        )

    # ── Option B: Refinement tournament ─────────────────────────────────────
    _rprint("\n  [cyan]Starting APOL refinement pipeline ...[/cyan]")
    _rprint(f"  [dim]Up to {MAX_CYCLES} cycles. You approve every change before it's saved.[/dim]\n")

    cycles_run = 0

    for cycle in range(1, MAX_CYCLES + 1):
        cycles_run = cycle
        _rprint(f"  [bold]Cycle {cycle} / {MAX_CYCLES}[/bold]")
        _rprint("  Calling apol-refine ...")

        try:
            improved_md = _call_refine(current_skill_md, feedback, summary)
        except Exception as e:
            _rprint(f"  [red]Refine failed: {e}[/red]")
            _rprint("  [yellow]Falling back to UNCERTIFIED publish.[/yellow]")
            return ApolResult(
                certified=False,
                score=score,
                skill_md=current_skill_md,
                kpi_scores=kpis,
                cycles_run=cycles_run,
            )

        # Show diff and ask creator to confirm
        _rprint("\n  [bold cyan]Proposed changes to SKILL.md:[/bold cyan]")
        _show_diff(current_skill_md, improved_md)

        confirm = _ask("\n  Accept these changes? [Y/N]: ")
        if confirm != "Y":
            _rprint("  [yellow]Changes rejected — publishing as UNCERTIFIED.[/yellow]")
            return ApolResult(
                certified=False,
                score=score,
                skill_md=current_skill_md,
                kpi_scores=kpis,
                cycles_run=cycles_run,
            )

        # Creator accepted — save improved version and re-score
        current_skill_md = improved_md
        skill_md_path.write_text(current_skill_md, encoding="utf-8")
        _rprint("  [green]Changes saved to SKILL.md[/green]")

        # Re-score
        _rprint("  Re-scoring improved SKILL.md ...")
        try:
            result = _call_judge(current_skill_md)
        except Exception as e:
            _rprint(f"  [yellow]Re-score failed ({e}) — accepting improvement at previous score[/yellow]")
            break

        score    = float(result.get("composite", 0.0))
        _fb      = result.get("feedback", {})
        kpis     = {
            "kpi2": {"score": result.get("kpi2", 1), "feedback": _fb.get("kpi2", "")},
            "kpi3": {"score": result.get("kpi3", 1), "feedback": _fb.get("kpi3", "")},
            "kpi4": {"score": result.get("kpi4", 1), "feedback": _fb.get("kpi4", "")},
            "kpi5": {"score": result.get("kpi5", 0), "feedback": _fb.get("kpi5", "")},
        }
        summary  = result.get("summary", "")
        feedback = _fb
        cert_id  = result.get("cert_id", None)

        _show_score(score, kpis, summary, cycle=cycle)

        if score >= CERTIFIED_THRESHOLD:
            _rprint(f"  [bold green]CERTIFIED! Score {score:.2f} meets threshold after {cycle} cycle(s)[/bold green]")
            return ApolResult(
                certified=True,
                score=score,
                skill_md=current_skill_md,
                cert_id=cert_id,
                kpi_scores=kpis,
                cycles_run=cycles_run,
            )

        if cycle < MAX_CYCLES:
            _rprint(f"  [yellow]Score {score:.2f} still below threshold. Running cycle {cycle+1} ...[/yellow]\n")
        else:
            _rprint(f"  [yellow]Max cycles reached. Final score: {score:.2f}[/yellow]")

    # Max cycles exhausted or loop broken — still below threshold after improvements
    _rprint("\n  [yellow]APOL pipeline complete — score did not reach threshold.[/yellow]")
    _rprint("  [dim]Your improved SKILL.md has been saved. You can re-run 'zforge publish' to try again.[/dim]\n")

    still_choice = _ask("  Publish current version as UNCERTIFIED? [Y/N]: ")
    if still_choice == "Y":
        return ApolResult(
            certified=False,
            score=score,
            skill_md=current_skill_md,
            kpi_scores=kpis,
            cycles_run=cycles_run,
        )

    _rprint("  [dim]Publish cancelled. Edit SKILL.md and re-run 'zforge publish' when ready.[/dim]")
    sys.exit(0)
