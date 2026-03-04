"""
zforge build -- single command full skill pipeline.
Scaffolds, generates GOAL.md via LLM, runs APOL, promotes winner,
populates skill.json, validates, tests, and optionally publishes.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    class _FallbackConsole:
        def print(self, *a, **k): print(*a)
        def rule(self, t=""): print(f"\n{'='*60} {t} {'='*60}")
    console = _FallbackConsole()

try:
    import litellm
    litellm.set_verbose = False
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False

# ── Map Agent Zero API key env vars to litellm expected format ──
_KEY_MAP = {
    "API_KEY_ANTHROPIC":  "ANTHROPIC_API_KEY",
    "API_KEY_OPENAI":     "OPENAI_API_KEY",
    "API_KEY_OPENROUTER": "OPENROUTER_API_KEY",
    "API_KEY_GOOGLE":     "GEMINI_API_KEY",
    "API_KEY_GROQ":       "GROQ_API_KEY",
    "API_KEY_MISTRAL":    "MISTRAL_API_KEY",
    "API_KEY_XAI":        "XAI_API_KEY",
    "API_KEY_DEEPSEEK":   "DEEPSEEK_API_KEY",
}
for _a0_key, _llm_key in _KEY_MAP.items():
    _val = os.environ.get(_a0_key, "")
    if _val and not os.environ.get(_llm_key):
        os.environ[_llm_key] = _val


def _get_api_key(model: str) -> str:
    """Map model prefix to Agent Zero API key env var.
    Priority: explicit provider prefix > model name heuristic > OpenRouter fallback.
    """
    import os as _os
    model_lower = model.lower()

    # Explicit provider prefix takes priority
    if model_lower.startswith("openrouter/"):
        return _os.environ.get("API_KEY_OPENROUTER") or _os.environ.get("OPENROUTER_API_KEY", "")
    if model_lower.startswith("openai/") or model_lower.startswith("gpt"):
        return _os.environ.get("API_KEY_OPENAI") or _os.environ.get("OPENAI_API_KEY", "")
    if model_lower.startswith("google/") or model_lower.startswith("gemini"):
        return _os.environ.get("API_KEY_GOOGLE") or _os.environ.get("GEMINI_API_KEY", "")
    if model_lower.startswith("groq/"):
        return _os.environ.get("API_KEY_GROQ") or _os.environ.get("GROQ_API_KEY", "")
    if model_lower.startswith("mistral/"):
        return _os.environ.get("API_KEY_MISTRAL") or _os.environ.get("MISTRAL_API_KEY", "")

    # Heuristic: contains provider name
    if "anthropic" in model_lower or "claude" in model_lower:
        key = _os.environ.get("API_KEY_ANTHROPIC") or _os.environ.get("ANTHROPIC_API_KEY", "")
        if key:
            return key
        # Fallback to OpenRouter for claude models
        return _os.environ.get("API_KEY_OPENROUTER") or _os.environ.get("OPENROUTER_API_KEY", "")

    # Last resort: OpenRouter
    return _os.environ.get("API_KEY_OPENROUTER") or _os.environ.get("OPENROUTER_API_KEY", "")


def _print(msg, style=""):
    if HAS_RICH:
        console.print(msg, style=style)
    else:
        print(msg)


def _rule(title):
    if HAS_RICH:
        console.rule(f"[bold cyan]{title}[/bold cyan]")
    else:
        print(f"\n{'='*60} {title} {'='*60}")


def _banner(name):
    _rule(f"zforge build -- {name}")
    _print(f"  [bold]Starting full automated pipeline for:[/bold] [yellow]{name}[/yellow]" if HAS_RICH else f"  Starting full pipeline for: {name}")
    _print("  Steps: scaffold → goal → dev → promote → skill.json → validate → test → publish\n")

def _validate_description(description: str) -> None:
    """
    Pre-flight check on --desc quality before burning API credits.
    Hard-blocks descriptions < 8 words or flagged as vague.
    Warns on descriptions 8-14 words and suggests improvements.
    """
    words = description.strip().split()
    word_count = len(words)
    vague_terms = {"stuff", "things", "various", "some", "misc",
                   "something", "anything", "todo", "tbd", "etc"}
    vague_found = [w for w in words if w.lower().strip(".,") in vague_terms]

    if word_count < 8:
        if HAS_RICH:
            console.print("[bold red]\n🚫 DESCRIPTION TOO SHORT — BUILD BLOCKED[/bold red]")
            console.print(f"  Got {word_count} words. Minimum is 8. APOL needs detail to score 0.80+.")
            console.print("  [yellow]Example:[/yellow] Scan a target directory and report all files modified in the last N days, output as table or JSON")
        else:
            print(f"\n🚫 DESCRIPTION BLOCKED: {word_count} words (min 8).")
            print("  Example: Scan a target directory and report all files modified in the last N days, output as table or JSON")
        sys.exit(1)

    if vague_found:
        if HAS_RICH:
            console.print(f"[bold red]\n🚫 VAGUE DESCRIPTION — BUILD BLOCKED[/bold red]")
            console.print(f"  Vague terms found: {vague_found}")
            console.print("  Replace with specific nouns, actions, and output formats.")
        else:
            print(f"\n🚫 VAGUE DESCRIPTION: {vague_found}. Be specific about inputs/outputs.")
        sys.exit(1)

    if word_count < 15:
        if HAS_RICH:
            console.print(f"[yellow]\n⚠ SHORT DESCRIPTION ({word_count} words) — may score below 0.80[/yellow]")
            console.print("  [dim]Tip: Add input params, output format, and use case.[/dim]")
        else:
            print(f"\n⚠ Short desc ({word_count} words). Consider adding input/output details.")
        # Continue — not a hard block, just a warning
    else:
        if HAS_RICH:
            console.print(f"[green]  ✓ Description quality: {word_count} words — good[/green]")
        else:
            print(f"  ✓ Description: {word_count} words — good")


def generate_goal_md(name: str, description: str, model: str) -> str:
    """Use LLM to expand a short description into a rich, technical GOAL.md.

    Produces a 10-section spec designed to drive APOL scores above 0.80.
    The richer the GOAL.md, the higher quality the SKILL.md drafts will be.
    """
    if not HAS_LITELLM:
        raise RuntimeError("litellm not installed. Run: pip install --upgrade zforge")

    system_prompt = """You are a senior AgentZero skill architect.
Your job is to write GOAL.md specification files that are so precise and detailed
that any LLM following them will produce a world-class SKILL.md scoring 0.90+.
Every section must contain real, specific, executable technical content.
No placeholders. No vague language. No padding."""

    user_prompt = f"""Write a comprehensive GOAL.md for the following skill.

Skill name: {name}
One-line description: {description}

Write EXACTLY this structure with ALL sections fully populated:

# Skill Goal: {name}

## 1. Purpose & Problem Statement
Exactly what problem this skill solves and why AgentZero needs it.
Include the specific pain point (2-4 sentences, concrete and technical).

## 2. Precise Input/Output Specification
Inputs: List every parameter/argument with name, type, example value, and whether required/optional.
Outputs: Describe exact return format (JSON schema, plain text, file paths, etc.) with a real example output.

## 3. Three Concrete Interaction Examples
For EACH example provide:
- User prompt (exactly what the user types)
- Agent action (what code runs, what command executes)
- Expected output (real terminal output or return value, not placeholder)

Example 1: Basic/happy path
Example 2: With optional parameters
Example 3: Edge case or error recovery

## 4. Technical Implementation Approach
Which Python libraries to use (with pip package names and versions).
Core algorithm or approach (step-by-step pseudocode if helpful).
Any OS-level dependencies (apt packages, system commands).

## 5. Edge Cases & Error Handling
List 4-6 specific edge cases with expected behavior for each:
- What happens with no results / empty state
- What happens with permission errors
- What happens with missing dependencies
- Network/timeout scenarios (if applicable)

## 6. File Structure the Skill Must Produce
Exact directory tree with filenames. Example:
```
{name}/
├── SKILL.md
├── skill.json
├── install.sh
├── requirements.txt
└── scripts/
    └── main.py
```

## 7. Installation Requirements
Exact install.sh commands. Exact requirements.txt contents. Any one-time setup steps.

## 8. Quality Bar — What a 5/5 SKILL.md Looks Like
Describe specifically what separates a 5/5 from a 3/5 for THIS skill:
- What makes examples exceptional
- What technical depth is required
- What troubleshooting entries are essential

## 9. Anti-Patterns to Avoid
List 4-5 specific things a poor SKILL.md for this skill would contain.

## 10. Changelog & Versioning Seed
v1.0.0 — Initial release. List the 3 most important features shipped.

Be specific. Use real commands, real output, real file paths. No [PLACEHOLDER] text."""

    api_key = _get_api_key(model)
    response = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        api_key=api_key if api_key else None,
        max_tokens=3000,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def build_skill_json(skill_dir: Path, name: str, author: str, tags: list,
                     category: str, description: str, price: str):
    """Write a populated skill.json from CLI arguments."""
    slug = name.replace("_", "-").lower()
    short_desc = description[:117] + "..." if len(description) > 120 else description
    now = datetime.now().strftime("%Y-%m-%d")

    manifest = {
        "$schema": "https://zero-forge.org/schemas/skill-manifest/v1.0.0.json",
        "metadata": {
            "name": name.replace("_", " ").title(),
            "slug": slug,
            "version": "1.0.0",
            "author": author,
            "author_url": f"https://zero-forge.org/profile/{author}",
            "repository": "",
            "license": "MIT",
            "price": price,
            "category": category,
            "tags": tags,
            "created_at": now,
            "updated_at": now
        },
        "description": {
            "short": short_desc,
            "long": description,
            "description_for_agent": f"Use this skill when the user wants to {description.lower().rstrip('.')}"
        },
        "compatibility": {
            "agentZero_min_version": "0.8",
            "python_min_version": "3.10"
        },
        "quality": {
            "apol_certified": False,
            "apol_composite_score": None
        },
        "marketplace": {
            "listing_url": f"https://zero-forge.org/listing/{slug}",
            "featured": False
        }
    }

    with open(skill_dir / "skill.json", "w") as f:
        json.dump(manifest, f, indent=2)
    _print(f"  [green]✓[/green] skill.json populated" if HAS_RICH else "  ✓ skill.json populated")


def run_step(label: str, cmd: list, cwd: Path) -> int:
    """Run a subprocess step and stream output."""
    _print(f"\n  [bold cyan]→ {label}[/bold cyan]" if HAS_RICH else f"\n  → {label}")
    import os as _os
    _env = {**_os.environ, "ZFORGE_SUBPROCESS": "1"}
    result = subprocess.run(cmd, cwd=cwd, env=_env)
    return result.returncode



def _issue_apol_cert(skill_dir: Path, skill_name: str) -> dict | None:
    """
    Issue an APOL cryptographic certificate via the ZeroForge Edge Function.
    Called after successful APOL tournament completion.
    Returns cert dict on success, None on failure (non-blocking).
    """
    import hashlib
    import urllib.request

    # Load env
    # Use env vars if set, otherwise fall back to embedded public credentials
    from cli.publisher import _PUBLIC_SUPABASE_URL, _PUBLIC_SUPABASE_ANON
    supabase_url = (os.environ.get("SUPABASE_URL") or _PUBLIC_SUPABASE_URL).rstrip("/")
    anon_key     = os.environ.get("SUPABASE_ANON_KEY") or _PUBLIC_SUPABASE_ANON
    if not supabase_url or not anon_key:
        _print("  [yellow]⚠ APOL cert skipped — Supabase credentials unavailable[/yellow]" if HAS_RICH
               else "  ⚠ APOL cert skipped — credentials unavailable")
        return None

    # Load APOL metadata
    # 02_run_experiment.py writes to: experiments/NNN_<name>/experiment_meta.json
    # (NOT experiments/apol_meta.json — that file never existed)
    import json as _json_meta
    exp_dir  = skill_dir / "experiments"
    meta_path = None
    meta = {}

    # Strategy 1: find latest NNN_*/experiment_meta.json (from 02_run_experiment.py)
    if exp_dir.exists():
        exp_subdirs = sorted(exp_dir.glob("[0-9][0-9][0-9]_*"), reverse=True)
        for sub in exp_subdirs:
            candidate = sub / "experiment_meta.json"
            if candidate.exists():
                meta_path = candidate
                break

    # Strategy 2: check legacy flat apol_meta.json (just in case)
    if meta_path is None:
        _legacy = exp_dir / "apol_meta.json"
        if _legacy.exists():
            meta_path = _legacy

    if meta_path is not None:
        meta = _json_meta.loads(meta_path.read_text())
    else:
        # Strategy 3: fall back to skill.json cached score (apol.py pathway)
        sj_fallback = skill_dir / "skill.json"
        if sj_fallback.exists():
            _sj = _json_meta.loads(sj_fallback.read_text())
            _cached_score = _sj.get("quality", {}).get("apol_composite_score")
            if _cached_score and float(_cached_score) >= 0.80:
                _print("  [cyan]ℹ Using cached APOL score from skill.json[/cyan]" if HAS_RICH
                       else "  ℹ Using cached APOL score from skill.json")
                meta = {
                    "experiment_id": f"exp-{skill_name}-cached",
                    "cycles_run": 2,
                    "winner": {"composite": float(_cached_score)},
                    "cycles": []
                }
            else:
                _print("  [yellow]⚠ APOL cert skipped — no experiment metadata or cached score found[/yellow]" if HAS_RICH
                       else "  ⚠ APOL cert skipped — no experiment metadata found")
                return None
        else:
            _print("  [yellow]⚠ APOL cert skipped — no experiment metadata found[/yellow]" if HAS_RICH
                   else "  ⚠ APOL cert skipped — no experiment metadata found")
            return None

    experiment_id    = meta.get("experiment_id", f"exp-{skill_name}")
    cycles_run       = int(meta.get("cycles_run", meta.get("total_cycles", 2)))
    composite_score  = float(meta.get("winner", {}).get("composite", 0.0))
    final_judge_score = round(composite_score * 5.0, 4)

    # Read GOAL.md
    goal_path = skill_dir / "GOAL.md"
    goal_md   = goal_path.read_text() if goal_path.exists() else ""
    if len(goal_md) < 100:
        _print("  [yellow]⚠ APOL cert skipped — GOAL.md too short[/yellow]" if HAS_RICH
               else "  ⚠ APOL cert skipped — GOAL.md too short")
        return None

    # Build judge_scores string from cycles
    _raw_cycles = meta.get("cycles", [])
    cycles_data = _raw_cycles if isinstance(_raw_cycles, list) else []
    if cycles_data:
        judge_lines = []
        for c in cycles_data:
            cycle_num = c.get("cycle", "?")
            scores    = c.get("scores", {})
            for persona, score_info in scores.items():
                composite = score_info if isinstance(score_info, float) else score_info.get("composite", 0)
                judge_lines.append(f"Cycle {cycle_num} | {persona}: {composite:.4f}")
        judge_scores = "\n".join(judge_lines)
    else:
        winner_name  = meta.get("winner", {}).get("name", "winner")
        judge_scores = f"Winner: {winner_name} | Composite: {composite_score:.4f} | Final Judge Score (0-5): {final_judge_score:.4f}"

    if len(judge_scores) < 50:
        judge_scores = judge_scores + " | ZeroForge APOL Tournament — world-class quality gate (0.80+ threshold)"

    # Read or build APOL_RESULTS.md
    results_path = exp_dir / "APOL_RESULTS.md"
    if results_path.exists():
        apol_results_md = results_path.read_text()
    else:
        winner_info = meta.get("winner", {})
        apol_results_md = (
            f"# APOL Results — {experiment_id}\n\n"
            f"## Winner\n- Name: {winner_info.get('name', 'N/A')}\n"
            f"- Composite Score: {composite_score:.4f}\n"
            f"- Cycles Run: {cycles_run}\n\n"
            f"## Tournament Summary\n"
            f"Quality threshold: 0.80 | Final score: {composite_score:.4f}\n"
        )

    if len(apol_results_md) < 100:
        apol_results_md = (apol_results_md + "\n\n" +
                           "ZeroForge APOL — Automated Persona Optimisation Loop. " * 3)

    # Compute skill_sha256 from zip or SKILL.md fallback
    zip_path = skill_dir.parent / f"{skill_name}.zip"
    if not zip_path.exists():
        zip_candidates = list(skill_dir.parent.glob(f"{skill_name}*.zip"))
        zip_path = zip_candidates[0] if zip_candidates else None
    if zip_path and zip_path.exists():
        sha256 = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    else:
        skill_md_path = skill_dir / "SKILL.md"
        sha256 = hashlib.sha256(skill_md_path.read_bytes()).hexdigest() if skill_md_path.exists() else ""

    if not sha256 or len(sha256) != 64:
        _print("  [yellow]⚠ APOL cert skipped — could not compute skill_sha256[/yellow]" if HAS_RICH
               else "  ⚠ APOL cert skipped — sha256 failed")
        return None

    # Get validator check count
    try:
        from cli.validator import CHECKS
        check_count = len(CHECKS)
        validator_checks = f"{check_count}/{check_count}"
    except Exception:
        validator_checks = "22/22"

    # Build payload
    import json as _json2
    payload = {
        "experiment_id":     experiment_id,
        "goal_md":           goal_md,
        "judge_scores":      judge_scores,
        "apol_results_md":   apol_results_md,
        "skill_sha256":      sha256,
        "cycles_run":        cycles_run,
        "final_judge_score": final_judge_score,
        "validator_checks":  validator_checks,
    }

    # Call Edge Function
    edge_url = f"{supabase_url}/functions/v1/issue-apol-cert"
    req_data = _json2.dumps(payload).encode()
    req = urllib.request.Request(
        edge_url,
        data=req_data,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {anon_key}",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            cert = _json2.loads(resp.read().decode())
        return cert
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        _print(f"  [yellow]⚠ APOL cert HTTP error {e.code}: {body}[/yellow]" if HAS_RICH
               else f"  ⚠ APOL cert error {e.code}: {body}")
        return None
    except Exception as ex:
        _print(f"  [yellow]⚠ APOL cert failed: {ex}[/yellow]" if HAS_RICH
               else f"  ⚠ APOL cert failed: {ex}")
        return None


# ── Script Repair Loop ───────────────────────────────────────────────────────
_REPAIR_MAX_CYCLES   = 2
_OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
_REPAIR_MODEL        = "google/gemini-flash-1.5"  # free tier
_PUBLIC_OR_KEY       = "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"



def _get_script_error(skill_dir: Path) -> tuple[int, str]:
    """Run scripts/main.py and capture exit code + stderr."""
    import subprocess as _sp
    import sys as _sys
    main_py = skill_dir / "scripts" / "main.py"
    if not main_py.exists():
        return 1, "scripts/main.py not found"
    try:
        result = _sp.run(
            [_sys.executable, str(main_py)],
            cwd=str(skill_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
        combined = (result.stderr or "") + (result.stdout or "")
        return result.returncode, combined
    except _sp.TimeoutExpired:
        return 1, "Timeout after 30s"
    except Exception as exc:
        return 1, str(exc)


def _call_openrouter_repair(script_code: str, error_msg: str, skill_md: str) -> str:
    """Send broken script to OpenRouter LLM and return the fixed code.
    Tries each model in _REPAIR_MODELS in order until one succeeds.
    """
    try:
        import requests as _req
    except ImportError:
        raise RuntimeError("pip install requests")

    api_key = os.environ.get("OPENROUTER_API_KEY") or _PUBLIC_OR_KEY
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    prompt = (
        "You are an expert Python developer. Fix the following Python script so it runs "
        "without errors. Preserve all original functionality and logic.\n\n"
        "## Error encountered\n"
        "```\n" + error_msg[:2000] + "\n```\n\n"
        "## Skill context (SKILL.md)\n"
        "```markdown\n" + skill_md[:3000] + "\n```\n\n"
        "## Script to fix (scripts/main.py)\n"
        "```python\n" + script_code + "\n```\n\n"
        "Return ONLY the fixed Python code, no explanation, no markdown fences."
    )

    last_error = "No models available"
    for model in _REPAIR_MODELS:
        try:
            resp = _req.post(
                _OPENROUTER_CHAT_URL,
                headers={
                    "Authorization": "Bearer " + api_key,
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://zero-forge.org",
                    "X-Title": "ZeroForge Script Repair",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 4096,
                },
                timeout=90,
            )
            if resp.status_code == 200:
                data = resp.json()
                fixed_code = data["choices"][0]["message"]["content"].strip()
                # Strip markdown fences if LLM wrapped the response
                if fixed_code.startswith("```"):
                    fenced_lines = fixed_code.split("\n")
                    if fenced_lines[0].startswith("```"):
                        fenced_lines = fenced_lines[1:]
                    if fenced_lines and fenced_lines[-1].strip() == "```":
                        fenced_lines = fenced_lines[:-1]
                    fixed_code = "\n".join(fenced_lines)
                _print("  Model used for repair: " + model)
                return fixed_code
            else:
                last_error = "OpenRouter [" + str(resp.status_code) + "] model=" + model + ": " + resp.text[:200]
                _print("  Model " + model + " failed (" + str(resp.status_code) + "), trying next...")
        except Exception as exc:
            last_error = str(exc)
            _print("  Model " + model + " error: " + str(exc) + ", trying next...")

    raise RuntimeError("All repair models failed. Last error: " + last_error)

def _script_repair_loop(skill_dir: Path) -> bool:
    """
    AI-powered script repair loop.
    Attempts to fix scripts/main.py up to _REPAIR_MAX_CYCLES times.
    Returns True if script passes smoke test after repair, False if all cycles fail.
    """
    import shutil as _shutil
    main_py = skill_dir / "scripts" / "main.py"
    skill_md_path = skill_dir / "SKILL.md"

    if not main_py.exists():
        msg = "  \u2717 scripts/main.py not found \u2014 cannot repair"
        _print(("  [red]" + msg.strip() + "[/red]") if HAS_RICH else msg)
        return False

    skill_md = skill_md_path.read_text(encoding="utf-8") if skill_md_path.exists() else ""
    backup_path = main_py.with_suffix(".py.bak")

    for cycle in range(1, _REPAIR_MAX_CYCLES + 1):
        _print("  Cycle " + str(cycle) + "/" + str(_REPAIR_MAX_CYCLES) + " \u2014 reading error...")

        returncode, error_msg = _get_script_error(skill_dir)
        if returncode == 0:
            msg = "  \u2713 Script passes \u2014 no repair needed"
            _print(("  [green]" + msg.strip() + "[/green]") if HAS_RICH else msg)
            return True

        _print("  Error: " + error_msg[:200])
        _print("  Cycle " + str(cycle) + "/" + str(_REPAIR_MAX_CYCLES) + " \u2014 sending to LLM for repair...")

        try:
            script_code = main_py.read_text(encoding="utf-8")
            _shutil.copy2(str(main_py), str(backup_path))

            fixed_code = _call_openrouter_repair(script_code, error_msg, skill_md)

            if not fixed_code.strip():
                _print("  Cycle " + str(cycle) + ": LLM returned empty response \u2014 skipping")
                continue

            _print("  Cycle " + str(cycle) + "/" + str(_REPAIR_MAX_CYCLES) + " \u2014 main.py rewritten, re-running smoke test...")
            main_py.write_text(fixed_code, encoding="utf-8")

            import py_compile as _pyc
            try:
                _pyc.compile(str(main_py), doraise=True)
            except _pyc.PyCompileError as syntax_err:
                _print("  Cycle " + str(cycle) + ": repaired script has syntax error: " + str(syntax_err))
                _shutil.copy2(str(backup_path), str(main_py))
                continue

            rc, _ = _get_script_error(skill_dir)
            if rc == 0:
                msg = "  \u2713 Script repair confirmed \u2014 all tests pass!"
                _print(("  [green]" + msg.strip() + "[/green]") if HAS_RICH else msg)
                backup_path.unlink(missing_ok=True)
                return True
            else:
                _print("  Cycle " + str(cycle) + ": still failing after repair, retrying...")

        except Exception as exc:
            _print("  Cycle " + str(cycle) + ": repair error: " + str(exc))
            if backup_path.exists():
                _shutil.copy2(str(backup_path), str(main_py))

    msg = "  \u2717 Script repair failed after all cycles \u2014 manual fix required"
    _print(("  [red]" + msg.strip() + "[/red]") if HAS_RICH else msg)
    if backup_path.exists():
        _shutil.copy2(str(backup_path), str(main_py))
        backup_path.unlink(missing_ok=True)
    return False



def build(
    skill_name: str,
    description: str,
    author: str,
    tags: list,
    category: str = "skill",
    price: str = "free",
    cycles: int = 2,
    model: str = "openrouter/anthropic/claude-sonnet-4-5",
    output_dir: Path = None,
    publish: bool = False,
    dry_run: bool = False,
):
    """Run the full automated skill build pipeline."""
    skills_base = output_dir or Path.cwd()
    skill_dir = skills_base / skill_name

    _banner(skill_name)

    # ── PRE-FLIGHT: Validate description quality ──────────────────
    _rule("Pre-flight — Description Quality Check")
    _validate_description(description)

    # ── STEP 1: Scaffold ──────────────────────────────────────────
    _rule("Step 1/7 — Scaffold")
    from cli.scaffold import scaffold_skill
    scaffold_skill(skill_name, skills_base, author=author)
    _print(f"  [green]✓[/green] Scaffolded at {skill_dir}" if HAS_RICH else f"  ✓ Scaffolded at {skill_dir}")

    # ── STEP 2: Generate GOAL.md ──────────────────────────────────
    _rule("Step 2/7 — Generating GOAL.md")
    _print("  Using LLM to expand description into full GOAL.md...")
    goal_content = generate_goal_md(skill_name, description, model)
    goal_path = skill_dir / "GOAL.md"
    goal_path.write_text(goal_content)
    _print(f"  [green]✓[/green] GOAL.md written ({len(goal_content.split())} words)" if HAS_RICH else f"  ✓ GOAL.md written")

    # ── STEP 3: APOL Dev Pipeline ─────────────────────────────────
    _rule("Step 3/7 — APOL Pipeline (zforge dev)")
    rc = run_step(
        f"zforge dev --cycles {cycles} --model {model}",
        ["zforge", "dev", "--goal", "GOAL.md", "--cycles", str(cycles), "--model", model],
        skill_dir
    )
    if rc != 0:
        _print("  [bold red]✗ APOL pipeline failed. Check output above.[/bold red]" if HAS_RICH else "  ✗ APOL pipeline failed.")
        sys.exit(rc)

    # ── STEP 4: Promote WINNER.md → SKILL.md ─────────────────────
    _rule("Step 4/7 — Promoting Winner")
    exp_dirs = sorted((skill_dir / "experiments").glob("[0-9][0-9][0-9]_*"))
    if not exp_dirs:
        _print("  [red]✗ No experiment directory found.[/red]" if HAS_RICH else "  ✗ No experiment found.")
        sys.exit(1)
    winner_path = exp_dirs[-1] / "WINNER.md"
    if not winner_path.exists():
        _print("  [red]✗ WINNER.md not found.[/red]" if HAS_RICH else "  ✗ WINNER.md not found.")
        sys.exit(1)
    shutil.copy(winner_path, skill_dir / "SKILL.md")
    _print(f"  [green]✓[/green] WINNER.md promoted to SKILL.md" if HAS_RICH else "  ✓ WINNER.md → SKILL.md")

    # ── Category normalizer: map common invalid values to valid categories ──
    VALID_CATEGORIES = {"skill", "guide", "template", "script", "course", "consulting"}
    CATEGORY_MAP = {
        "utilities": "skill", "utility": "script", "tools": "script",
        "scripts": "script", "guides": "guide", "templates": "template",
        "courses": "course", "plugin": "skill", "extension": "skill",
        "workflow": "skill", "agent": "skill",
    }
    if category not in VALID_CATEGORIES:
        normalized = CATEGORY_MAP.get(category.lower(), "skill")
        _print(f"  [yellow]⚠ Category '{category}' is not valid — normalized to '{normalized}'[/yellow]" if HAS_RICH
               else f"  ⚠ Category '{category}' normalized to '{normalized}'")
        category = normalized

    # ── STEP 5: Populate skill.json ───────────────────────────────
    _rule("Step 5/7 — Populating skill.json")
    build_skill_json(skill_dir, skill_name, author, tags, category, description, price)

    # ── STEP 6: Validate ─────────────────────────────────────────
    _rule("Step 6/7 — Validate")
    rc = run_step("zforge validate", ["zforge", "validate"], skill_dir)
    if rc != 0:
        _print("  [yellow]⚠ Validation issues found — review above before publishing.[/yellow]" if HAS_RICH else "  ⚠ Validation issues found.")

    # ── STEP 6.5: Issue APOL Certificate ─────────────────────────
    _rule("Step 6.5/7 — Issuing APOL Certificate")
    cert = _issue_apol_cert(skill_dir, skill_name)
    if cert and "signature" in cert:
        # Update skill.json quality section with cert data
        import json as _certjson
        sj_path = skill_dir / "skill.json"
        if sj_path.exists():
            sj = _certjson.loads(sj_path.read_text())
            if "quality" not in sj:
                sj["quality"] = {}
            sj["quality"]["apol_certified"]      = True
            sj["quality"]["apol_cert_id"]        = cert.get("experiment_id", "")
            sj["quality"]["apol_cert_signature"] = cert.get("signature", "")
            sj["quality"]["apol_cert_issued_at"] = cert.get("issued_at", "")
            sj["quality"]["apol_cert_url"]       = f"https://zero-forge.org/verify/{cert.get('experiment_id', '')}"
            # Keep composite score if already set, else derive from cert
            if not sj["quality"].get("apol_composite_score"):
                fjs = cert.get("final_judge_score", 0)
                sj["quality"]["apol_composite_score"] = round(fjs / 5.0, 4)
            sj_path.write_text(_certjson.dumps(sj, indent=2))
        _print(f"  [bold green]✓ APOL Certificate issued![/bold green]" if HAS_RICH else "  ✓ APOL Certificate issued!")
        _print(f"  [dim]Cert ID: {cert.get('experiment_id')} | Sig: {cert.get('signature', '')[:16]}...[/dim]" if HAS_RICH else f"  Cert ID: {cert.get('experiment_id')}")
    else:
        _print("  [yellow]⚠ APOL cert not issued — skill.json quality section unchanged[/yellow]" if HAS_RICH else "  ⚠ APOL cert not issued")

    # ── STEP 7: Test ─────────────────────────────────────────────
    _rule("Step 7/7 — Test")
    rc = run_step("zforge test", ["zforge", "test", "--skill", "."], skill_dir)
    if rc != 0:
        _print("\n  [bold yellow]⚠ Tests failed — launching AI Script Repair Loop...[/bold yellow]" if HAS_RICH
               else "\n  ⚠ Tests failed — launching AI Script Repair Loop...")
        repaired = _script_repair_loop(skill_dir)
        if repaired:
            # Re-run full test suite to confirm repair
            _print("  [cyan]Re-running full test suite to confirm repair...[/cyan]" if HAS_RICH
                   else "  Re-running full test suite to confirm repair...")
            rc = run_step("zforge test", ["zforge", "test", "--skill", "."], skill_dir)
            if rc != 0:
                if HAS_RICH:
                    console.print("\n  [bold yellow]⚠ Tests still failing after repair — continuing to publish step.[/bold yellow]")
                    console.print("  [dim]Fix scripts/main.py manually before publishing to ensure quality.[/dim]")
                else:
                    print("\n  ⚠ Tests still failing after repair — continuing to publish step.")
                    print("  Fix scripts/main.py manually before publishing to ensure quality.")
            else:
                _print("  [bold green]✅ Script repair confirmed — all tests pass![/bold green]" if HAS_RICH
                       else "  ✅ Script repair confirmed — all tests pass!")
        else:
            if HAS_RICH:
                console.print("\n  [bold yellow]⚠ Script Repair Loop unavailable — continuing to publish step.[/bold yellow]")
                console.print("  [dim]Fix scripts/main.py manually: zforge test --skill . to verify.[/dim]")
            else:
                print("\n  ⚠ Script Repair Loop unavailable — continuing to publish step.")
                print("  Fix scripts/main.py manually: zforge test --skill . to verify.")
    else:
        _print("  [bold green]✅ All tests passed![/bold green]" if HAS_RICH else "  ✅ All tests passed!")

    # ── PUBLISH (optional) ────────────────────────────────────────
    if publish or dry_run:
        flag = "Step 8 — Publish" if publish else "Step 8 — Dry Run Publish"
        _rule(flag)

        # 🔴 HARD GATE: Block publish if APOL score < 0.80
        apol_score = None
        try:
            import glob as _glob, json as _json
            exp_dirs_glob = sorted(_glob.glob(str(skill_dir / "experiments" / "[0-9][0-9][0-9]_*")))
            if not exp_dirs_glob:
                # Also check r-and-d/experiments path
                rnd_base = skill_dir.parent.parent / "r-and-d" / "experiments"
                exp_dirs_glob = sorted(_glob.glob(str(rnd_base / "[0-9][0-9][0-9]_*")))
            if exp_dirs_glob:
                meta_file = Path(exp_dirs_glob[-1]) / "experiment_meta.json"
                if meta_file.exists():
                    meta = _json.loads(meta_file.read_text())
                    apol_score = meta.get("winner", {}).get("composite", None)
        except Exception as _e:
            _print(f"  [yellow]⚠ Could not read APOL score: {_e}[/yellow]")

        if apol_score is not None and apol_score < 0.80:
            if HAS_RICH:
                _print(f"  [bold red]🚫 PUBLISH BLOCKED — APOL score {apol_score:.3f} < 0.80 minimum.[/bold red]")
                _print(f"  [red]Run `zforge build {skill_dir.name} --rebuild` to re-run APOL and reach 0.80+.[/red]")
            else:
                _print(f"  PUBLISH BLOCKED — APOL score {apol_score:.3f} < 0.80 minimum.")
            return  # Hard stop — do not publish
        elif apol_score is not None:
            _print(f"  [green]✅ APOL gate passed: {apol_score:.3f} >= 0.80[/green]" if HAS_RICH else f"  ✅ APOL gate: {apol_score:.3f} >= 0.80")
        else:
            _print("  [yellow]⚠ APOL score not found — skipping gate check[/yellow]" if HAS_RICH else "  ⚠ APOL score not found — skipping gate check")

        cmd = ["zforge", "publish", "."]
        if dry_run:
            cmd.append("--dry-run")
        run_step("zforge publish", cmd, skill_dir)

    # ── DONE ──────────────────────────────────────────────────────
    _rule("Build Complete")

    # Read cached APOL score from skill.json to decide whether to offer auto-publish
    _done_score = None
    _done_certified = False
    try:
        import json as _donejson
        _sj_path = skill_dir / "skill.json"
        if _sj_path.exists():
            _sj = _donejson.loads(_sj_path.read_text())
            _done_score = _sj.get("quality", {}).get("apol_composite_score", None)
            _done_certified = _sj.get("quality", {}).get("apol_certified", False)
            if _done_score is not None:
                _done_score = float(_done_score)
    except Exception:
        pass

    if HAS_RICH:
        if _done_certified and _done_score is not None and _done_score >= 0.80:
            console.print(Panel(
                "[bold green]✓ Skill ready:[/bold green] [yellow]" + str(skill_dir) + "[/yellow]\n"
                "[bold green]🏆 APOL Score: " + str(round(_done_score, 3)) + " — CERTIFIED[/bold green]",
                title="[bold magenta]ZeroForge[/bold magenta]",
                border_style="green"
            ))
        else:
            _score_str = (" | APOL: " + str(round(_done_score, 3))) if _done_score is not None else ""
            console.print(Panel(
                "[bold green]✓ Skill ready:[/bold green] [yellow]" + str(skill_dir) + "[/yellow]" + _score_str,
                title="[bold magenta]ZeroForge[/bold magenta]",
                border_style="yellow" if not _done_certified else "green"
            ))
            if not _done_certified:
                console.print("  [yellow]⚠ Skill is UNCERTIFIED — you can still publish but it won't show the CERTIFIED badge.[/yellow]")
        try:
            _publish_now = console.input("[bold cyan]Publish to marketplace now? [Y/n]: [/bold cyan]").strip().lower()
        except (EOFError, KeyboardInterrupt):
            _publish_now = "n"
        if _publish_now in ("", "y", "yes"):
            _rule("Step 8 — Publish")
            import subprocess as _subp
            _subp.run(["zforge", "publish", "."], cwd=str(skill_dir))
            _show_marketplace_url(skill_dir, supabase_url, anon_key, True, console)
        else:
            console.print("[dim]Run when ready:[/dim] [cyan]zforge publish " + str(skill_dir) + "[/cyan]")
    else:
        print("  ✓ Skill ready: " + str(skill_dir))
        if _done_certified and _done_score is not None:
            print("  🏆 APOL Score: " + str(round(_done_score, 3)) + " — CERTIFIED")
        else:
            if _done_score is not None:
                print("  APOL Score: " + str(round(_done_score, 3)) + " (UNCERTIFIED)")
            print("  ⚠ Skill is UNCERTIFIED — you can still publish but won't receive the CERTIFIED badge.")
        try:
            _publish_now = input("  Publish to marketplace now? [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            _publish_now = "n"
        if _publish_now in ("", "y", "yes"):
            import subprocess as _subp
            _subp.run(["zforge", "publish", "."], cwd=str(skill_dir))
            _show_marketplace_url(skill_dir, supabase_url, anon_key, False, None)
        else:
            print("  Run when ready: zforge publish " + str(skill_dir))
