#!/usr/bin/env python3
"""
02_run_experiment.py  --  ZeroForge APOL experiment pipeline.

Generates multiple SKILL.md candidates from GOAL.md, judges each
with the APOL rubric, and saves the winner to:

    <skill_dir>/experiments/NNN_<name>/WINNER.md
    <skill_dir>/experiments/NNN_<name>/experiment_meta.json

Usage:
    python 02_run_experiment.py --goal GOAL.md --name cpu_check \
        --cycles 3 --model openrouter/anthropic/claude-sonnet-4-5
"""
import argparse
import json
import os
import re
import sys
import time

from cli._constants import CERTIFIED_THRESHOLD
from datetime import datetime, timezone
from pathlib import Path

# ── litellm import ─────────────────────────────────────────────────────────
try:
    import litellm
    litellm.set_verbose = False
except ImportError:
    print("ERROR: litellm not installed. Run: pip install litellm", file=sys.stderr)
    sys.exit(1)

# ── Key mapping (Agent Zero env vars -> litellm expected names) ────────────
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
for _a0key, _llmkey in _KEY_MAP.items():
    _v = os.environ.get(_a0key, "")
    if _v and not os.environ.get(_llmkey):
        os.environ[_llmkey] = _v

# ── Fallback model chain ───────────────────────────────────────────────────
FALLBACK_MODELS = [
    "openrouter/anthropic/claude-sonnet-4-5",
    "openrouter/anthropic/claude-3-haiku",
    "openrouter/google/gemini-flash-1.5",
    "openrouter/meta-llama/llama-3.1-8b-instruct:free",
    "openrouter/mistralai/mistral-7b-instruct:free",
]


def _llm_call(model, messages, max_tokens=4096):
    """Call litellm with fallback chain on rate-limit or error."""
    models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]
    last_err = None
    for m in models_to_try:
        try:
            resp = litellm.completion(
                model=m,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"  [warn] {m} failed: {e}")
            last_err = e
            time.sleep(1)
    raise RuntimeError("All models failed. Last error: " + str(last_err))


# ── SKILL.md generation ────────────────────────────────────────────────────

GENERATE_SYSTEM = (
    "You are a world-class AgentZero skill author. "
    "Your SKILL.md files are the gold standard on the ZeroForge marketplace. "
    "Every section must be filled with real, executable, copy-paste-ready content. "
    "No placeholders. No vague language. No padding. "
    "The output must be a single, complete SKILL.md file and nothing else."
)


def _generate_user_prompt(name, goal_content):
    return (
        "Using the specification below, write a complete SKILL.md for the '" + name + "' skill.\n\n"
        "RULES:\n"
        "- Follow the exact SKILL.md structure shown\n"
        "- Every section must contain real, specific content\n"
        "- Include at least 2 worked examples with real input/output\n"
        "- Include error handling for at least 3 common failure modes\n"
        "- Keep instructions numbered and scannable\n"
        "- Total length: 300-700 words\n\n"
        "REQUIRED STRUCTURE:\n"
        "# " + name + "\n"
        "## Overview\n"
        "## Requirements\n"
        "## Usage\n"
        "### Inputs\n"
        "### Outputs\n"
        "## Step-by-Step Instructions\n"
        "## Examples\n"
        "### Example 1\n"
        "### Example 2\n"
        "## Error Handling\n"
        "## Notes\n\n"
        "---\n"
        "SPECIFICATION:\n" + goal_content + "\n"
        "---\n\n"
        "Write the SKILL.md now:"
    )


def generate_candidate(name, goal_content, model, attempt):
    """Generate one SKILL.md candidate using LLM."""
    print(f"  Generating candidate {attempt}...", flush=True)
    messages = [
        {"role": "system", "content": GENERATE_SYSTEM},
        {"role": "user",   "content": _generate_user_prompt(name, goal_content)},
    ]
    temp = min(0.9, 0.5 + attempt * 0.1)
    try:
        resp = litellm.completion(
            model=model,
            messages=messages,
            max_tokens=4096,
            temperature=temp,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return _llm_call(model, messages, max_tokens=4096)


# ── APOL scoring ───────────────────────────────────────────────────────────

JUDGE_SYSTEM = (
    "You are an APOL (AgentZero Prompt Object Language) skill quality judge. "
    "Score SKILL.md files on 4 KPIs. Be strict — 1.0 means truly excellent. "
    "Respond ONLY with valid JSON matching the schema. No prose, no markdown fences."
)


def _judge_user_prompt(skill_md):
    return (
        "Score this SKILL.md using the APOL rubric.\n\n"
        "KPI DEFINITIONS:\n"
        "- kpi2: Purpose & problem statement clarity (0.0-1.0)\n"
        "  1.0 = crystal clear problem, specific pain point, explains WHY\n"
        "  0.0 = vague or missing\n"
        "- kpi3: Input/Output specification completeness (0.0-1.0)\n"
        "  1.0 = all params typed, required/optional flagged, output format precise\n"
        "  0.0 = missing or vague I/O\n"
        "- kpi4: Example quality with real data (0.0-1.0)\n"
        "  1.0 = 2+ examples, realistic inputs, exact expected outputs\n"
        "  0.0 = no examples or placeholder data\n"
        "- kpi5: Error handling coverage (0.0-1.0)\n"
        "  1.0 = 3+ specific errors with cause and fix\n"
        "  0.0 = no error handling\n\n"
        'Respond with ONLY this JSON (no markdown, no extra text):\n'
        '{"kpi2": 0.0, "kpi3": 0.0, "kpi4": 0.0, "kpi5": 0.0,'
        ' "composite": 0.0, "feedback": "improvement tip"}\n\n'
        "SKILL.md to score:\n---\n" + skill_md[:6000] + "\n---"
    )


def score_candidate(skill_md, model):
    """Score a SKILL.md with the APOL rubric via LLM judge."""
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user",   "content": _judge_user_prompt(skill_md)},
    ]
    raw = _llm_call(model, messages, max_tokens=512)

    # Strip any markdown fences the model might add despite instructions
    raw = re.sub(r"^```[a-z]*\n", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\n```$", "", raw, flags=re.MULTILINE).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{[^{}]+\}", raw, re.DOTALL)
        if m:
            data = json.loads(m.group())
        else:
            raise ValueError("Judge returned unparseable response: " + raw[:200])

    kpis = [
        float(data.get("kpi2", 0)),
        float(data.get("kpi3", 0)),
        float(data.get("kpi4", 0)),
        float(data.get("kpi5", 0)),
    ]
    data["composite"] = round(sum(kpis) / len(kpis), 4)
    return data


# ── Experiment directory management ───────────────────────────────────────

def _next_experiment_dir(experiments_base, name):
    """Return next numbered experiment dir: 001_name, 002_name, ..."""
    existing = sorted(experiments_base.glob("[0-9][0-9][0-9]_*"))
    n = len(existing) + 1
    safe_name = re.sub(r"[^a-z0-9_-]", "_", name.lower())
    return experiments_base / f"{n:03d}_{safe_name}"


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ZeroForge APOL experiment pipeline")
    parser.add_argument("--goal",   default="GOAL.md")
    parser.add_argument("--name",   required=True)
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--model",  default="openrouter/anthropic/claude-sonnet-4-5")
    args = parser.parse_args()

    skill_dir        = Path.cwd()
    goal_path        = Path(args.goal) if Path(args.goal).is_absolute() else skill_dir / args.goal
    experiments_base = skill_dir / "experiments"
    experiments_base.mkdir(exist_ok=True)

    if not goal_path.exists():
        print(f"ERROR: GOAL.md not found at {goal_path}", file=sys.stderr)
        sys.exit(1)

    goal_content = goal_path.read_text().strip()

    print("")
    print("  ZeroForge APOL Experiment Pipeline")
    print(f"  Skill  : {args.name}")
    print(f"  Goal   : {goal_path}")
    print(f"  Cycles : {args.cycles}")
    print(f"  Model  : {args.model}")
    print(f"  Output : {experiments_base}")
    print("")

    candidates = []
    for i in range(1, args.cycles + 1):
        print(f"  -- Cycle {i}/{args.cycles} --")
        try:
            skill_md = generate_candidate(args.name, goal_content, args.model, i)
            print(f"  Generated {len(skill_md.split())} words", flush=True)
        except Exception as e:
            print(f"  [error] Generation failed for cycle {i}: {e}", file=sys.stderr)
            continue

        print("  Scoring with APOL rubric...", flush=True)
        try:
            scores = score_candidate(skill_md, args.model)
        except Exception as e:
            print(f"  [error] Scoring failed for cycle {i}: {e}", file=sys.stderr)
            scores = {"kpi2": 0, "kpi3": 0, "kpi4": 0, "kpi5": 0,
                      "composite": 0, "feedback": "scoring failed"}

        c = scores.get("composite", 0)
        print(
            f"  Score  : {c:.3f}  "
            f"(kpi2={scores.get('kpi2', 0):.2f}  "
            f"kpi3={scores.get('kpi3', 0):.2f}  "
            f"kpi4={scores.get('kpi4', 0):.2f}  "
            f"kpi5={scores.get('kpi5', 0):.2f})"
        )
        print(f"  Tip    : {scores.get('feedback', '')}", flush=True)
        candidates.append({"skill_md": skill_md, "scores": scores, "cycle": i})

    if not candidates:
        print("ERROR: All generation cycles failed.", file=sys.stderr)
        sys.exit(1)

    winner   = max(candidates, key=lambda c: c["scores"].get("composite", 0))
    w_scores = winner["scores"]
    print(f"\n  == WINNER: Cycle {winner['cycle']}  score={w_scores['composite']:.3f} ==")

    exp_dir = _next_experiment_dir(experiments_base, args.name)
    exp_dir.mkdir(parents=True, exist_ok=True)

    for cand in candidates:
        (exp_dir / f"candidate_{cand['cycle']:02d}.md").write_text(cand["skill_md"])

    (exp_dir / "WINNER.md").write_text(winner["skill_md"])

    meta = {
        "experiment_id": exp_dir.name,
        "skill_name":    args.name,
        "model":         args.model,
        "cycles":        args.cycles,
        "generated_at":  datetime.now(timezone.utc).isoformat(),
        "candidates": [
            {
                "cycle":     c["cycle"],
                "composite": c["scores"].get("composite", 0),
                "kpi2":      c["scores"].get("kpi2", 0),
                "kpi3":      c["scores"].get("kpi3", 0),
                "kpi4":      c["scores"].get("kpi4", 0),
                "kpi5":      c["scores"].get("kpi5", 0),
                "feedback":  c["scores"].get("feedback", ""),
            } for c in candidates
        ],
        "winner": {
            "cycle":     winner["cycle"],
            "composite": w_scores.get("composite", 0),
            "kpi2":      w_scores.get("kpi2", 0),
            "kpi3":      w_scores.get("kpi3", 0),
            "kpi4":      w_scores.get("kpi4", 0),
            "kpi5":      w_scores.get("kpi5", 0),
            "feedback":  w_scores.get("feedback", ""),
        },
    }
    (exp_dir / "experiment_meta.json").write_text(json.dumps(meta, indent=2))

    print(f"  Saved  : {exp_dir}")
    print(f"  Winner : {exp_dir / 'WINNER.md'}")
    print("")

    composite = w_scores.get("composite", 0)
    if composite >= CERTIFIED_THRESHOLD:
        print(f"  APOL PASSED: {composite:.3f} >= {CERTIFIED_THRESHOLD}  -- ready to publish")
    else:
        print(f"  APOL score {composite:.3f} < {CERTIFIED_THRESHOLD}  -- consider refining GOAL.md and re-running")

    sys.exit(0)


if __name__ == "__main__":
    main()
