# zeroforge

---

**Version:** 2.0.0
**Author:** colin-charles
**AgentZero Version:** 0.8+
**Category:** Dev Tools
**Tags:** skill-development, apol, automation, zeroforge, publishing, quality-assurance, cli
**License:** MIT
**Price:** Free
**Updated:** 2026-03-02

---


## ⚡ Agent Zero — Install zforge in 60 Seconds

> **This section is for Agent Zero.** If a user says *"install zforge"* or *"set up ZeroForge"*, follow these exact steps.

### Step 1 — Check if already installed
```bash
zforge --version 2>/dev/null && echo "ALREADY INSTALLED" || echo "NOT INSTALLED"
```

If output says `ALREADY INSTALLED` → skip to Step 4.

### Step 2 — Clone the zforge repository
```bash
git clone https://github.com/colin-charles/zforge ~/.zforge 2>/dev/null || (cd ~/.zforge && git pull)
```

### Step 3 — Install the zforge CLI
```bash
cd ~/.zforge
python3 -m venv venv
source venv/bin/activate
pip install -q -e .
```

This will:
- Create a Python venv at `~/.zforge/venv`
- Install all dependencies (typer, rich)
- Install the `zforge` command into the venv

### Step 4 — Activate venv and verify
```bash
source ~/.zforge/venv/bin/activate
zforge --help
```

Expected output shows commands: `login`, `whoami`, `new`, `build`, `validate`, `test`, `publish`, `install`, `run`, `list`, `search`, `info`.

### Step 5 — Tell the user it's ready

Report back: *"✅ zforge is installed and ready. You can now install skills, create skills, or browse the ZeroForge marketplace at https://zero-forge.org"*

---

## 🚀 Agent Zero — Run a Skill in One Command

> If a user says *"install and run [skill-name]"* or *"run the [skill-name] skill from ZeroForge"*, follow these steps.

### Step 1 — Ensure zforge is installed
Follow the install steps above if `zforge --version` fails.

### Step 2 — Activate venv
```bash
source ~/.zforge/venv/bin/activate
```

### Step 3 — Run the skill
```bash
# Replace <skill-name> with the actual skill slug (e.g. system-health-report)
zforge run <skill-name>
```

`zforge run` will automatically:
1. Search the ZeroForge marketplace for the skill
2. Download and install it
3. Execute the skill
4. Show the output

### Example — Run the system health report
```bash
source ~/.zforge/venv/bin/activate
zforge run system-health-report
```

### Step 4 — Show user the output

Copy the terminal output and present it to the user in a readable format.

---

## 📋 Agent Zero — List Available Skills

```bash
source ~/.zforge/venv/bin/activate
zforge list
```

Returns a table of all published skills on the ZeroForge marketplace with name, description, and author.

---

## Description

`zeroforge` gives AgentZero the ability to research, design, generate, test, package, and publish new AgentZero skills ready for submission to the ZeroForge marketplace. It implements the full **APOL pipeline** (Automated Persona-driven Output Loop) — an iterative, judge-driven R&D process that produces publication-quality SKILL.md files through competitive persona evaluation and structured improvement cycles.

Version 2.0 adds the `zforge` CLI tool, enabling a single-command developer experience from scaffold to publish. The skill covers the complete lifecycle: `zforge new` → `zforge dev` → `zforge test` → `zforge validate` → `zforge publish`.

Designed for ZeroForge contributors, power users, and AI developers who want to build high-quality, reusable AgentZero capabilities at scale without manual trial and error.

---

## Requirements

| Requirement | Details |
|---|---|
| AgentZero Version | 0.8+ |
| Python | 3.10+ |
| API Keys | LLM API key (already configured in AgentZero) |
| Environment Variables | `ANTHROPIC_API_KEY` or compatible LLM key via litellm |
| pip dependencies | `litellm>=1.0.0`, `rich>=13.0.0`, `typer[all]>=0.9.0`, `pydantic>=2.0.0`, `requests>=2.28.0` |
| Optional | `SUPABASE_ANON_KEY` in `~/.zforge/.env` for `zforge publish` |

---

## File Structure

```
zeroforge/
  SKILL.md                        ← This file
  SkillTest.md                    ← Declarative test suite
  skill.json                      ← Machine-readable manifest
  install.sh                      ← Installation script
  requirements.txt                ← Python dependencies
  pyproject.toml                  ← pip install -e . entrypoint
  cli/
    __init__.py
    main.py                       ← zforge CLI entrypoint (typer)
    scaffold.py                   ← zforge new logic
    runner.py                     ← zforge dev logic
    validator.py                  ← zforge validate logic
    tester.py                     ← zforge test logic
    publisher.py                  ← zforge publish logic
  scripts/
    01_define_goal.py             ← Interactive GOAL.md wizard
    02_run_experiment.py          ← APOL pipeline runner (automated)
    03_package_skill.py           ← ZIP packager
    04_validate_skill.py          ← Structural validator
    test_runner.py                ← SkillTest.md test runner
  templates/
    SkillTest.md                  ← Test format specification
    skill.json                    ← Manifest template with placeholders
```

---

## Installation

### Option A — Install via pip (recommended)

```bash
pip install zforge
```

Verify installation:
```bash
zforge --version
```

### Option B — Install from source

```bash
git clone https://github.com/colin-charles/zforge ~/.zforge
cd ~/.zforge
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Dependencies

```bash
pip install litellm rich typer[all] pydantic requests
```

---

## Usage Examples

### Example 1 — Scaffold a new skill from scratch

**User prompt:**
> "Create a new skill called web_screenshot"

**Agent runs:**
```bash
zforge new web_screenshot
cd web_screenshot
# Edit GOAL.md to describe what the skill does
```

**Output:**
```
╭─────────────── ZeroForge ─────────────────╮
│ Skill scaffolded! →                        │
│ ./web_screenshot                           │
│                                            │
│  1. Edit GOAL.md                           │
│  2. Run zforge dev                         │
│  3. Run zforge test --skill .              │
╰────────────────────────────────────────────╯
```

Created files:
```
web_screenshot/
  GOAL.md         ← fill in skill purpose
  SKILL.md        ← stub with all section headers
  SkillTest.md    ← test suite template
  skill.json      ← manifest template
  install.sh
  requirements.txt
  scripts/main.py
```

---

### Example 2 — Run the APOL experiment pipeline

**User prompt:**
> "Generate a SKILL.md for my web_screenshot skill using APOL"

**Agent runs:**
```bash
cd web_screenshot
zforge dev --goal GOAL.md --cycles 3 --model anthropic/claude-sonnet-4-5
```

**What happens:**
1. Three AI personas (Technical-Precision, UX-Obsessed, Example-First) each write a SKILL.md draft
2. Each draft is scored by programmatic metric (7 structural checks) + LLM judge (5 KPIs)
3. Lowest-scoring persona is eliminated after cycle 1
4. Remaining two personas improve over cycles 2-3 using OPRO trajectory injection
5. Winner is declared by composite score (0.4 × programmatic + 0.6 × judge)
6. `WINNER.md` is saved to `experiments/001_<name>/`

**Output:**
```
experiments/001_web_screenshot/
  WINNER.md              ← best SKILL.md
  APOL_RESULTS.md        ← full scoring table
  experiment_meta.json   ← cert metadata
  cycles/cycle_01/ ...   ← all drafts + judge scores
```

---

### Example 3 — Run the test suite

**User prompt:**
> "Test the web_screenshot skill"

**Agent runs:**
```bash
zforge test --skill ./web_screenshot
```

**Output (rich table):**
```
┌──────────────────────┬──────────────┬────────┬──────────────────────┐
│ Test                 │ Type         │ Status │ Detail               │
├──────────────────────┼──────────────┼────────┼──────────────────────┤
│ test_required_files  │ file_exists  │ PASS   │ 4/4 files present    │
│ test_apol_metric     │ apol_metric  │ PASS   │ score=0.9267 ≥ 0.70  │
│ test_script_syntax   │ shell        │ PASS   │ exit 0               │
│ test_validate_script │ shell        │ PASS   │ exit 0               │
│ test_template_exists │ file_exists  │ PASS   │ skill.json present   │
└──────────────────────┴──────────────┴────────┴──────────────────────┘
5/5 PASS — exit 0
```

---

### Example 4 — Validate skill quality

**User prompt:**
> "Validate my skill before publishing"

**Agent runs:**
```bash
zforge validate --skill ./web_screenshot
```

Checks: required sections, no placeholders, word count ≥300, code blocks, examples, troubleshooting, metadata header.

---

### Example 5 — Publish to ZeroForge marketplace

**User prompt:**
> "Publish the web_screenshot skill to the marketplace"

**Agent runs:**
```bash
# Dry run first (no submission)
zforge publish ./web_screenshot --dry-run

# Real submission
zforge publish ./web_screenshot
```

**What publish does:**
1. Validates `skill.json` against Pydantic model (name, slug, version, author, license, category, tags, short description ≤120 chars, description_for_agent ≥10 words)
2. Loads APOL cert data from `experiments/*/experiment_meta.json` if present
3. Packages skill into a ZIP (excludes: `.git`, `__pycache__`, `*.egg-info`, `venv`, `experiments/`)
4. POSTs listing payload to Supabase REST API with `status: pending`
5. Prints listing ID and marketplace URL

**Requires** `SUPABASE_ANON_KEY` in `~/.zforge/.env`

---

## Configuration

| Setting | Default | Description |
|---|---|---|
| `--model` | `anthropic/claude-sonnet-4-5` | LLM model for APOL via litellm |
| `--cycles` | `3` | Max APOL improvement cycles |
| `--goal` | `GOAL.md` | Path to goal definition file |
| `--skill` | `.` (cwd) | Skill directory for test/validate/publish |
| `--dry-run` | `false` | Validate only, skip Supabase POST |
| `SUPABASE_ANON_KEY` | (from .env) | Marketplace submission credentials |
| `CONVERGENCE_SCORE` | `0.85` | Auto-stop threshold for APOL cycles |
| `PASS_THRESHOLD` | `0.72` | Minimum composite score to pass |

---

## Scripts Reference

| Script | Command | Purpose |
|---|---|---|
| `01_define_goal.py` | `python scripts/01_define_goal.py` | Interactive GOAL.md wizard |
| `02_run_experiment.py` | `zforge dev` or `python scripts/02_run_experiment.py --goal GOAL.md --name <name>` | Full APOL pipeline |
| `03_package_skill.py` | `python scripts/03_package_skill.py --skill .` | ZIP packager |
| `04_validate_skill.py` | `zforge validate` or `python scripts/04_validate_skill.py --skill .` | Structural validator |
| `test_runner.py` | `zforge test` or `python scripts/test_runner.py --skill .` | SkillTest.md runner |

---

## Troubleshooting

**Problem:** `zforge: command not found` after install
**Solution:** Ensure venv is activated: `source ~/.zforge/venv/bin/activate`. Re-install: `pip install -e .`

**Problem:** `litellm.AuthenticationError` during `zforge dev`
**Solution:** Set your API key: `export ANTHROPIC_API_KEY=sk-ant-...` or configure in AgentZero settings.

**Problem:** `SUPABASE_ANON_KEY not found` during `zforge publish`
**Solution:** Add key to `~/.zforge/.env`: `SUPABASE_ANON_KEY=eyJ...`

**Problem:** `short description must be <= 120 chars` validation error
**Solution:** Edit `skill.json` → `description.short` and shorten to ≤120 characters.

**Problem:** APOL score below 0.70 threshold in test
**Solution:** Run `zforge validate --skill .` to see which of 7 checks are failing. Common fixes: add Troubleshooting section with ≥2 entries, add ≥3 usage examples, remove unfilled placeholder tokens.

**Problem:** `zforge publish` returns HTTP 401
**Solution:** Your `SUPABASE_ANON_KEY` may be expired or invalid. Retrieve current key from Supabase dashboard → Project Settings → API.

---

## Changelog

| Version | Date | Changes |
|---|---|---|
| 2.0.0 | 2026-02-28 | Added `zforge` CLI (new/dev/validate/test/publish), `publisher.py` with Pydantic validation, Supabase integration, `skill.json` manifest, `SkillTest.md` format |
| 1.1.0 | 2026-02-15 | Added `test_runner.py`, `SkillTest.md` declarative test format, `04_validate_skill.py` |
| 1.0.0 | 2026-02-01 | Initial release: APOL pipeline, `02_run_experiment.py`, 3-persona tournament |

---

## Support

- **GitHub:** https://github.com/colin-charles/zforge
- **Marketplace:** https://zero-forge.org/listing/zeroforge
- **Issues:** https://github.com/colin-charles/zforge/issues
- **Community:** ZeroForge Discord → #skill-dev channel

---

## License

MIT License — Copyright (c) 2026 ZeroForge. Free for personal and commercial use.
