# ZeroForge CLI — Code Index & Concordance

> **Last updated:** 2026-03-05  
> **CLI version:** 2.1.52  
> **Purpose:** Help any developer — even a junior — navigate the zforge codebase quickly.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [File Index](#2-file-index)
3. [Command → Code Reference](#3-command--code-reference)
4. [Data Flow: Skill Lifecycle](#4-data-flow-skill-lifecycle)
5. [Key Functions Index](#5-key-functions-index)
6. [Cross-Reference: Who Calls Whom](#6-cross-reference-who-calls-whom)
7. [External Services & APIs](#7-external-services--apis)
8. [Configuration Sources](#8-configuration-sources)
9. [Common Code Patterns](#9-common-code-patterns)
10. [Glossary](#10-glossary)

---

## 1. Architecture Overview

### How ZeroForge CLI Works (Big Picture)

ZeroForge (`zforge`) is a command-line tool that helps developers create, test, validate,
and publish **skills** (reusable AI agent capabilities) to the ZeroForge marketplace.

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER (Terminal)                          │
│                     $ zforge <command>                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      main.py (CLI Router)                       │
│  Typer app that routes commands to the right module:            │
│                                                                 │
│  new ──→ scaffold.py      validate ──→ validator.py             │
│  dev ──→ runner.py        test ──────→ tester.py                │
│  build ──→ builder.py     publish ───→ publisher.py             │
│  login/whoami ──→ (inline in main.py)                           │
│  list/search/install ──→ (inline, queries Supabase)             │
│  run ──→ (inline, downloads + executes skill)                   │
│  setup ──→ (inline, installs dependencies)                      │
└──────┬──────────┬──────────┬──────────┬────────────────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────────────┐
│scaffold  │ │validator │ │ builder  │ │     publisher           │
│.py       │ │.py       │ │.py       │ │     .py                 │
│          │ │          │ │          │ │                         │
│ Creates  │ │ Checks   │ │ Builds   │ │ Packages + uploads      │
│ skill    │ │ SKILL.md │ │ skill    │ │ to Supabase + triggers  │
│ from     │ │ + files  │ │ with AI  │ │ APOL certification      │
│ template │ │ + rules  │ │ assist   │ │                         │
└──────────┘ └──────────┘ └────┬─────┘ └────────────┬────────────┘
                               │                     │
                               ▼                     ▼
                          ┌──────────┐    ┌──────────────────────┐
                          │ apol.py  │    │   Supabase Cloud     │
                          │          │    │                      │
                          │ Local    │    │ ┌──────────────────┐ │
                          │ APOL     │    │ │ Edge Functions:  │ │
                          │ pipeline │    │ │ • submit-listing │ │
                          │ (client  │    │ │ • apol-judge     │ │
                          │  side)   │    │ │ • apol-refine    │ │
                          └──────────┘    │ └──────────────────┘ │
                                          │ ┌──────────────────┐ │
                                          │ │ Storage (zips)   │ │
                                          │ │ Database (lists) │ │
                                          │ └──────────────────┘ │
                                          └──────────────────────┘
```

### Two APOL Paths

- **Server-side (via publisher.py):** When you `zforge publish`, the `submit-listing` edge
  function calls `apol-judge` automatically. This is the **trusted** path — scores cannot be faked.
- **Client-side (via apol.py / builder.py):** When you `zforge build`, the CLI can optionally
  call the APOL endpoints directly for preview scoring. This is **informational only**.

---

## 2. File Index

### Core CLI Modules (`cli/`)

| File | Lines | Purpose |
|------|------:|---------|
| `main.py` | 1470 | **CLI entry point.** Defines all `zforge` commands using Typer. Routes to other modules. Also contains inline logic for `login`, `whoami`, `list`, `search`, `install`, `run`, `setup`. |
| `publisher.py` | 950 | **Publish pipeline.** Packages skills, uploads to Supabase Storage, submits metadata via edge function, displays APOL results. |
| `builder.py` | 1069 | **AI-assisted skill builder.** Generates SKILL.md from description using LLM, builds skill.json, runs script repair loops, optionally triggers local APOL scoring. |
| `apol.py` | 667 | **APOL certification client.** Calls the `apol-judge` and `apol-refine` edge functions. Displays KPI scores. Used by builder.py for preview scoring. |
| `scaffold.py` | 377 | **Skill scaffolding.** Creates a new skill directory from templates with SKILL.md, skill.json, scripts/, etc. |
| `validator.py` | 213 | **Skill validator.** Checks that a skill directory has all required files, valid JSON, correct SKILL.md structure, etc. |
| `tester.py` | 98 | **Test runner entry point.** Thin wrapper that calls `scripts/test_runner.py`. |
| `runner.py` | 151 | **Dev server.** Runs a skill in development mode for local testing. |
| `__init__.py` | 25 | **Version constant.** Holds `__version__ = "2.1.52"`. |

### Support Scripts (`cli/scripts/`)

| File | Lines | Purpose |
|------|------:|---------|
| `test_runner.py` | 429 | **Full test engine.** Parses `SkillTest.md`, runs test cases, checks assertions, reports pass/fail. |
| `02_run_experiment.py` | 563 | **R&D experiment runner.** Generates and scores skill candidates using LLMs. Used for APOL research, not normal CLI usage. |
| `__init__.py` | 0 | Empty. Makes `scripts/` a Python package. |

### Release Tooling (`scripts/`)

| File | Lines | Purpose |
|------|------:|---------|
| `release.py` | 271 | **Release automation.** Bumps version, updates changelogs (both repos), builds + publishes to PyPI, git commits + tags + pushes both repos. |

### Templates (`templates/`)

| File | Purpose |
|------|---------|
| `skill.json` | Template for skill metadata JSON. Used by scaffold.py. |
| `SkillTest.md` | Template for test definitions. Used by scaffold.py. |

### Config Files (root)

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python package config. Defines name, version, dependencies, entry points. |
| `requirements.txt` | Pip requirements for development. |
| `install.sh` | Quick-install script for users (curl-pipe-bash). |
| `CHANGELOG.md` | Version history with categorized changes. |
| `README.md` | Project documentation and usage guide. |
| `SKILL.md` | Meta-skill: describes zforge itself as an Agent Zero skill. |
| `LICENSE` | MIT license. |

---

## 3. Command → Code Reference

Where to find the code for each `zforge` command:

| Command | Defined In | Handler Function | Delegates To |
|---------|-----------|-------------------|---------------|
| `zforge` (no args) | main.py:194 | `_main()` | Shows help + update check |
| `zforge hello` | main.py:218 | `hello()` | — (inline) |
| `zforge login` | main.py:266 | `login()` | GitHub OAuth flow (inline) |
| `zforge whoami` | main.py:598 | `whoami()` | Reads ~/.zforge/config.json |
| `zforge info` | main.py:642 | `info()` | — (inline) |
| `zforge new` | main.py:687 | `new()` | `scaffold.scaffold_skill()` |
| `zforge dev` | main.py:709 | `dev()` | `runner.run_dev()` |
| `zforge validate` | main.py:731 | `validate()` | `validator.run_validate()` |
| `zforge test` | main.py:758 | `test()` | `tester.run_test()` |
| `zforge publish` | main.py:776 | `publish()` | `publisher.publish_skill()` |
| `zforge build` | main.py:802 | `build()` | `builder.build()` |
| `zforge list` | main.py:847 | `list_skills()` | Queries Supabase (inline) |
| `zforge search` | main.py:924 | `search()` | Queries Supabase (inline) |
| `zforge install` | main.py:981 | `install()` | Downloads from Supabase (inline) |
| `zforge setup` | main.py:1194 | `setup()` | Installs deps (inline) |
| `zforge run` | main.py:1291 | `run_skill()` | Downloads + executes (inline) |

---

## 4. Data Flow: Skill Lifecycle

### 4.1 Creating a Skill

```
$ zforge new my-skill
       │
       ▼
main.py:new() ──→ scaffold.scaffold_skill("my-skill")
                         │
                         ├── Creates directory: ./my-skill/
                         ├── Writes SKILL.md from template
                         ├── Writes skill.json from template
                         ├── Creates scripts/ directory
                         └── Creates SkillTest.md from template
```

### 4.2 Building a Skill (AI-Assisted)

```
$ zforge build
       │
       ▼
main.py:build() ──→ builder.build()
                         │
                         ├── Validates description length
                         ├── Gets LLM API key (OpenRouter)
                         ├── Calls OpenRouter to generate SKILL.md
                         ├── Builds skill.json metadata
                         ├── Runs script repair loop (if errors)
                         │     └── Calls _call_openrouter_repair()
                         ├── Optionally runs APOL preview
                         │     └── _issue_apol_cert() ──→ apol.run_apol_pipeline()
                         └── Shows marketplace URL
```

### 4.3 Publishing

```
$ zforge publish
       │
       ▼
main.py:publish() ──→ publisher.publish_skill()
       │
       ├── 1. Load credentials from ~/.zforge/config.json
       │      └── _load_zforge_credentials()
       │
       ├── 2. Verify API key with Supabase
       │      └── _verify_api_key(api_key)
       │
       ├── 3. Validate skill files exist
       │      └── Checks SKILL.md + skill.json
       │
       ├── 4. Package into zip (excluding junk)
       │      └── package_skill() ──→ _should_exclude()
       │
       ├── 5. Upload zip to Supabase Storage
       │      └── upload_to_storage() or upload_via_edge_function()
       │
       ├── 6. Submit metadata to edge function
       │      └── _submit_to_edge_function()
       │           │
       │           ▼  (SERVER-SIDE)
       │      submit-listing edge function
       │           ├── Validates payload
       │           ├── Calls apol-judge for scoring
       │           ├── Inserts/updates listing in database
       │           └── Returns score + certification status
       │
       └── 7. Display results
              └── Shows APOL score, certified badge, marketplace URL
```

### 4.4 APOL Certification (Detail)

```
Skill submitted ──→ submit-listing edge function
                         │
                         ├── Extracts skill_md from payload
                         ├── Calls apol-judge edge function
                         │     │
                         │     ├── Sends SKILL.md to OpenRouter LLM
                         │     ├── LLM scores on 5 KPIs (0.0-1.0):
                         │     │   • Completeness
                         │     │   • Clarity
                         │     │   • Modularity
                         │     │   • Usefulness
                         │     │   • Innovation
                         │     ├── Calculates composite score (average)
                         │     └── Returns scores + summary feedback
                         │
                         ├── If composite >= 0.80 → CERTIFIED ✅
                         ├── If composite <  0.80 → UNCERTIFIED (with feedback)
                         └── Stores score in listings table
```

---

## 5. Key Functions Index

Alphabetical listing of important functions with file and line number.

| Function | File | Line | Purpose |
|----------|------|-----:|---------|
| `_call_judge()` | apol.py | 232 | Send SKILL.md to apol-judge edge function, get KPI scores |
| `_call_openrouter_repair()` | builder.py | 619 | Ask LLM to fix broken skill scripts |
| `_call_refine()` | apol.py | 275 | Send SKILL.md + feedback to apol-refine for improvement suggestions |
| `_check_for_update()` | main.py | 78 | Check PyPI for newer zforge version |
| `_extract_github_handle()` | publisher.py | 806 | Parse GitHub username from author URL or string |
| `_fetch()` (install helper) | main.py | 1006 | Query Supabase for a skill listing by name or ID |
| `_get_api_key()` | builder.py | 74 | Find OpenRouter API key from env vars |
| `_get_script_error()` | builder.py | 589 | Run a skill script and capture any error output |
| `_is_placeholder()` | publisher.py | 195 | Check if a value looks like a placeholder (e.g., "your-name-here") |
| `_issue_apol_cert()` | builder.py | 390 | Run local APOL certification during build |
| `_load_apol_cert()` | publisher.py | 508 | Load APOL certificate file from skill directory |
| `_load_zforge_credentials()` | publisher.py | 49 | Read API key + handle from ~/.zforge/config.json |
| `_print()` | publisher.py | 147 | Print with Rich styling (or plain fallback) |
| `_rule()` | publisher.py | 157 | Print horizontal rule divider |
| `_save_zforge_config()` | main.py | 542 | Write API key + handle to ~/.zforge/config.json |
| `_script_repair_loop()` | builder.py | 693 | Iteratively fix skill script errors using LLM |
| `_should_exclude()` | publisher.py | 318 | Check if a file should be excluded from the skill zip |
| `_show_marketplace_url()` | builder.py | 774 | Display the marketplace URL after build |
| `_show_score()` | apol.py | 326 | Pretty-print APOL KPI scores with progress bars |
| `_submit_to_edge_function()` | publisher.py | 555 | POST listing payload to submit-listing edge function |
| `_verify_api_key()` | publisher.py | 60 | Verify API key is valid by checking Supabase |
| `build()` | builder.py | 791 | Main build orchestrator: LLM generation + packaging |
| `build_and_publish()` | release.py | 159 | Build Python package and upload to PyPI |
| `build_skill_json()` | builder.py | 288 | Generate skill.json metadata file |
| `bump_version()` | release.py | 67 | Update version in pyproject.toml + __init__.py |
| `check()` | test_runner.py | 51 | Assert a test condition, print pass/fail |
| `fetch_listing()` (run cmd) | main.py | 1328 | Fetch listing data for `zforge run` command |
| `generate_candidate()` | 02_run_experiment.py | 207 | Generate a SKILL.md candidate via LLM |
| `generate_goal_md()` | builder.py | 191 | Generate SKILL.md content using OpenRouter LLM |
| `git_push_website()` | release.py | 194 | Commit + push changelog to website repo |
| `git_push_zforge()` | release.py | 178 | Commit + tag + push CLI repo to GitHub |
| `hello()` | main.py | 223 | Display ASCII banner and system info |
| `install()` | main.py | 981 | Download and install a skill from marketplace |
| `list_skills()` | main.py | 847 | List all skills in the marketplace |
| `load_env()` | publisher.py | 167 | Load environment variables for Supabase connection |
| `login()` | main.py | 273 | GitHub OAuth PKCE login flow |
| `main()` | release.py | 209 | Release script entry point |
| `package_skill()` | publisher.py | 340 | Zip a skill directory for upload |
| `parse_skilltest()` | test_runner.py | 126 | Parse SkillTest.md into structured test cases |
| `publish_skill()` | publisher.py | 629 | Full publish pipeline: validate → package → upload → submit |
| `run_apol_pipeline()` | apol.py | 436 | Full APOL flow: judge → show scores → optionally refine |
| `run_dev()` | runner.py | 45 | Start skill in development/watch mode |
| `run_step()` | builder.py | 367 | Run a shell command as a build step |
| `run_test()` | tester.py | 43 | Entry point for `zforge test` |
| `run_tests()` | test_runner.py | 200 | Execute all parsed test cases |
| `run_validate()` | validator.py | 90 | Full validation check on skill directory |
| `scaffold_skill()` | scaffold.py | 198 | Create new skill from templates |
| `score_candidate()` | 02_run_experiment.py | 314 | Score a SKILL.md candidate using LLM judge |
| `search()` | main.py | 924 | Search marketplace by keyword |
| `setup()` | main.py | 1194 | Install zforge dependencies |
| `update_changelog_js()` | release.py | 123 | Add entry to website changelog.js |
| `update_changelog_md()` | release.py | 97 | Add entry to CHANGELOG.md |
| `upload_to_storage()` | publisher.py | 380 | Upload zip file to Supabase Storage bucket |
| `upload_via_edge_function()` | publisher.py | 448 | Alternative upload path via edge function |
| `whoami()` | main.py | 598 | Display current logged-in user info |

---

## 6. Cross-Reference: Who Calls Whom

### main.py calls:

| Command Function | Calls |
|------------------|-------|
| `_main()` | `_check_for_update()`, `_run_update_check()` |
| `new()` | `scaffold.scaffold_skill()` |
| `dev()` | `runner.run_dev()` |
| `validate()` | `validator.run_validate()` |
| `test()` | `tester.run_test()` |
| `publish()` | `publisher.publish_skill()` |
| `build()` | `builder.build()` |
| `login()` | `_save_zforge_config()`, `_print_zforge_login_success()` |
| `whoami()` | reads `~/.zforge/config.json` directly |
| `install()` | `_fetch()` → Supabase REST API |
| `list_skills()` | Supabase REST API directly |
| `search()` | Supabase REST API directly |
| `run_skill()` | `fetch_listing()` → Supabase REST API |

### publisher.py calls:

| Function | Calls |
|----------|-------|
| `publish_skill()` | `_load_zforge_credentials()`, `_verify_api_key()`, `package_skill()`, `upload_to_storage()`, `upload_via_edge_function()`, `_submit_to_edge_function()`, `_load_apol_cert()`, `_extract_github_handle()` |
| `package_skill()` | `_should_exclude()` |
| `_submit_to_edge_function()` | `requests.post()` → submit-listing edge function |
| `_verify_api_key()` | `requests.get()` → Supabase REST API |

### builder.py calls:

| Function | Calls |
|----------|-------|
| `build()` | `_validate_description()`, `_get_api_key()`, `generate_goal_md()`, `build_skill_json()`, `run_step()`, `_script_repair_loop()`, `_issue_apol_cert()`, `_show_marketplace_url()` |
| `_issue_apol_cert()` | `apol.run_apol_pipeline()` |
| `_script_repair_loop()` | `_get_script_error()`, `_call_openrouter_repair()` |
| `generate_goal_md()` | `requests.post()` → OpenRouter API |
| `_call_openrouter_repair()` | `requests.post()` → OpenRouter API |

### apol.py calls:

| Function | Calls |
|----------|-------|
| `run_apol_pipeline()` | `_call_judge()`, `_show_score()`, `_call_refine()`, `_show_diff()` |
| `_call_judge()` | `requests.post()` → apol-judge edge function |
| `_call_refine()` | `requests.post()` → apol-refine edge function |

### release.py calls:

| Function | Calls |
|----------|-------|
| `main()` | `bump_version()`, `update_changelog_md()`, `update_changelog_js()`, `build_and_publish()`, `git_push_zforge()`, `git_push_website()` |
| `build_and_publish()` | `run()` (shell commands) |
| `git_push_zforge()` | `run()` (git commands) |
| `git_push_website()` | `run()` (git commands) |

---

## 7. External Services & APIs

| Service | Used In | What For | Endpoint Pattern |
|---------|---------|----------|------------------|
| **Supabase Database** | publisher.py, main.py | Store/query skill listings | `{SUPABASE_URL}/rest/v1/listings` |
| **Supabase Storage** | publisher.py, main.py | Store/download skill zips | `{SUPABASE_URL}/storage/v1/object/skill-packages/` |
| **Supabase Edge Functions** | publisher.py, apol.py | submit-listing, apol-judge, apol-refine | `{SUPABASE_URL}/functions/v1/{name}` |
| **Supabase Auth** | main.py (login) | GitHub OAuth for user identity | `{SUPABASE_URL}/auth/v1/` |
| **OpenRouter** | builder.py, 02_run_experiment.py | LLM API for SKILL.md generation + script repair | `https://openrouter.ai/api/v1/chat/completions` |
| **PyPI** | release.py | Publish new CLI versions | `https://upload.pypi.org/legacy/` (via twine) |
| **GitHub** | main.py (login), release.py | OAuth provider + git push | OAuth flow + git CLI |

---

## 8. Configuration Sources

### Where Settings Come From

| Setting | Source | Used In | Notes |
|---------|--------|---------|-------|
| Supabase URL | Hardcoded | publisher.py, apol.py, main.py | Same URL across all modules |
| Supabase Anon Key | Hardcoded | publisher.py, main.py | Public key, safe to embed |
| Supabase Service Key | Env: `SUPABASE_SERVICE_ROLE_KEY` | publisher.py (storage upload) | Secret, never in client code |
| User API Key | `~/.zforge/config.json` | publisher.py | Created by `zforge login` |
| GitHub Handle | `~/.zforge/config.json` | publisher.py | Created by `zforge login` |
| OpenRouter API Key | Env: `OPENROUTER_API_KEY` | builder.py | For LLM calls during build |
| PyPI Token | Env: `PYPI_TOKEN` | release.py | For publishing releases |
| LLM Model | Env or defaults | builder.py | Default: `google/gemini-2.0-flash-001` |

### Config File: `~/.zforge/config.json`

```json
{
  "api_key": "zf_abc123...",
  "handle": "githubusername"
}
```

Created by `zforge login`. Permissions set to `chmod 600` (owner-only read/write).

---

## 9. Common Code Patterns

### Pattern 1: Rich Console Fallback

**Used in:** publisher.py, builder.py, apol.py, scaffold.py

```python
# Try to import Rich for pretty terminal output.
# If not installed, fall back to plain print().
try:
    from rich.console import Console
    console = Console()
    _use_rich = True
except ImportError:
    class _FallbackConsole:
        def print(self, *a, **k): print(*a)
        def rule(self, t=""): print(f"{'='*60} {t}")
    console = _FallbackConsole()
    _use_rich = False
```

**Why:** Rich is optional. The CLI must work even without it.

### Pattern 2: Pydantic Fallback

**Used in:** publisher.py

```python
# Try Pydantic v2 for payload validation, fall back to a simple wrapper
try:
    from pydantic import BaseModel, field_validator
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    # ... defines a dict-based fallback class
```

**Why:** Pydantic is a heavy dependency. For basic `zforge publish`, a dict wrapper suffices.

### Pattern 3: Helper Print Functions

**Used in:** publisher.py, builder.py, apol.py, validator.py

```python
def _print(msg, style=""):
    """Print with Rich styling if available, plain otherwise."""
    if _use_rich:
        console.print(msg, style=style)
    else:
        print(msg)

def _rule(title):
    """Print a horizontal rule with title."""
    if _use_rich:
        console.rule(title)
    else:
        print(f"\n{'='*60} {title} {'='*60}")
```

**Why:** Consistent output across all modules, degrades gracefully.

### Pattern 4: Supabase REST API Calls

**Used in:** publisher.py, main.py

```python
import requests

# All Supabase REST calls follow this pattern:
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/listings",
    headers={
        "apikey": ANON_KEY,                    # Always required
        "Authorization": f"Bearer {ANON_KEY}",  # Same key as Bearer
    },
    params={"select": "*", "title": f"eq.{name}"},
)
```

**Why:** Supabase PostgREST requires both `apikey` header and `Authorization` Bearer token.

### Pattern 5: Edge Function Calls

**Used in:** publisher.py, apol.py

```python
resp = requests.post(
    f"{SUPABASE_URL}/functions/v1/submit-listing",
    headers={
        "Authorization": f"Bearer {ANON_KEY}",
        "Content-Type": "application/json",
        "X-API-Key": api_key,  # User's personal API key
    },
    json=payload,
    timeout=120,  # APOL scoring takes time
)
```

**Why:** Edge functions authenticate via both Supabase anon key and user API key.

---

## 10. Glossary

| Term | Meaning |
|------|---------|
| **APOL** | Autonomous Proof-of-Learning. AI certification that scores skills on quality (0.0-1.0). Score >= 0.80 = Certified. |
| **Edge Function** | Serverless function on Supabase (Deno runtime). Used for submit-listing, apol-judge, apol-refine. |
| **KPI** | Key Performance Indicator. APOL scores on: Completeness, Clarity, Modularity, Usefulness, Innovation. |
| **Listing** | A marketplace entry for a skill. Stored in the `listings` Supabase table. |
| **Marketplace** | The ZeroForge web store at zero-forge.org where skills are browsed and installed. |
| **OpenRouter** | LLM API gateway that routes to various AI models (GPT, Claude, Gemini, etc.). |
| **PKCE** | Proof Key for Code Exchange. OAuth security extension that prevents authorization code interception. |
| **RLS** | Row Level Security. Supabase feature controlling who can read/write database rows. |
| **Scaffold** | Create a new skill directory with template files via `zforge new`. |
| **Service Key** | Supabase key with full database access. Only used server-side, never in client code. |
| **SKILL.md** | Main documentation file for a skill. Describes purpose, usage, prerequisites. Follows AgentSkills.io standard. |
| **skill.json** | Metadata file with name, version, author, tags, and other machine-readable info. |
| **SkillTest.md** | Test definition file. Contains test cases that `zforge test` runs against the skill. |
| **Supabase** | Backend-as-a-Service providing PostgreSQL database, file storage, auth, and edge functions. |
| **zforge** | The ZeroForge CLI tool. Installed via `pip install zforge`. |
| **ZeroForge** | The platform/ecosystem for creating and sharing Agent Zero skills. |

---

## Quick Navigation Tips

1. **"Where does command X start?"** → See [Section 3](#3-command--code-reference)
2. **"What does function Y do?"** → See [Section 5](#5-key-functions-index)
3. **"What calls what?"** → See [Section 6](#6-cross-reference-who-calls-whom)
4. **"Where are secrets/configs?"** → See [Section 8](#8-configuration-sources)
5. **"How does publishing work end-to-end?"** → See [Section 4.3](#43-publishing)
6. **"What is APOL?"** → See [Glossary](#10-glossary) + [Section 1](#two-apol-paths)

---

*Generated for ZeroForge CLI v2.1.52 — Update this file when adding new commands or major refactors.*
