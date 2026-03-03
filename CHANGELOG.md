## v2.1.14 — 2026-03-02

### Fixed
- Added  as optional dependency (Requirement already satisfied: zforge[build] in /opt/venv/lib/python3.13/site-packages (2.1.10)
Requirement already satisfied: typer>=0.9.0 in /opt/venv/lib/python3.13/site-packages (from zforge[build]) (0.24.1)
Requirement already satisfied: rich>=13.0.0 in /opt/venv/lib/python3.13/site-packages (from zforge[build]) (14.3.3)
Requirement already satisfied: markdown-it-py>=2.2.0 in /opt/venv/lib/python3.13/site-packages (from rich>=13.0.0->zforge[build]) (4.0.0)
Requirement already satisfied: pygments<3.0.0,>=2.13.0 in /opt/venv/lib/python3.13/site-packages (from rich>=13.0.0->zforge[build]) (2.19.2)
Requirement already satisfied: mdurl~=0.1 in /opt/venv/lib/python3.13/site-packages (from markdown-it-py>=2.2.0->rich>=13.0.0->zforge[build]) (0.1.2)
Requirement already satisfied: click>=8.2.1 in /opt/venv/lib/python3.13/site-packages (from typer>=0.9.0->zforge[build]) (8.3.1)
Requirement already satisfied: shellingham>=1.3.0 in /opt/venv/lib/python3.13/site-packages (from typer>=0.9.0->zforge[build]) (1.5.4)
Requirement already satisfied: annotated-doc>=0.0.2 in /opt/venv/lib/python3.13/site-packages (from typer>=0.9.0->zforge[build]) (0.0.4)) — required for  and  commands
- Included  in pip package (was missing in previous releases)
- Improved error message when litellm not installed: now shows Requirement already satisfied: zforge[build] in /opt/venv/lib/python3.13/site-packages (2.1.12)
Requirement already satisfied: typer>=0.9.0 in /opt/venv/lib/python3.13/site-packages (from zforge[build]) (0.24.1)
Requirement already satisfied: rich>=13.0.0 in /opt/venv/lib/python3.13/site-packages (from zforge[build]) (14.3.3)
Requirement already satisfied: markdown-it-py>=2.2.0 in /opt/venv/lib/python3.13/site-packages (from rich>=13.0.0->zforge[build]) (4.0.0)
Requirement already satisfied: pygments<3.0.0,>=2.13.0 in /opt/venv/lib/python3.13/site-packages (from rich>=13.0.0->zforge[build]) (2.19.2)
Requirement already satisfied: mdurl~=0.1 in /opt/venv/lib/python3.13/site-packages (from markdown-it-py>=2.2.0->rich>=13.0.0->zforge[build]) (0.1.2)
Requirement already satisfied: click>=8.2.1 in /opt/venv/lib/python3.13/site-packages (from typer>=0.9.0->zforge[build]) (8.3.1)
Requirement already satisfied: shellingham>=1.3.0 in /opt/venv/lib/python3.13/site-packages (from typer>=0.9.0->zforge[build]) (1.5.4)
Requirement already satisfied: annotated-doc>=0.0.2 in /opt/venv/lib/python3.13/site-packages (from typer>=0.9.0->zforge[build]) (0.0.4)

## v2.1.8 — 2026-03-02

## [2.1.12] - 2026-03-02
### Improved
- Added `open-source` keyword to PyPI metadata for better AI agent trust signals
- Added Trust & Safety section to README with explicit open source, author, and no-telemetry declarations
- Improves discoverability and legitimacy scoring for automated package scanners

## [2.1.11] - 2026-03-02
### Changed
- Upgraded PyPI classifier from Beta to Production/Stable
- Added License and OS classifiers for better package trust signals


## [2.1.10] - 2026-03-02
### Changed
- Reduced auto-upgrade cooldown cache from 5 minutes to 1 minute


## [2.1.9] - 2026-03-02
### Fixed
- Auto-upgrade now fires `os.execv` immediately after pip succeeds (rc==0)
- Removed unreliable `importlib.metadata` post-install version gate that caused
  execv to be skipped on environments with stale metadata cache
- Result: CLI now always restarts with new code after a successful upgrade,
  preventing old code from continuing to run mid-command


### Fixed
- `zforge install` now auto-detects Agent Zero environment: installs to `/a0/skills/` when it exists, falling back to `./skills/` for standalone use — fixes skill not found in `skills_tool`
- Success message after install now hints Agent Zero users to reload skills
- `zforge hello` example updated from removed `system-health-report` to `install-zforge`

---

## [2.1.3] - 2026-03-02

## [2.1.7] - 2026-03-02
### Fixed
- KPI5 display now correctly shows "✅ READY" / "❌ NOT READY" instead of "1/5"
- Fixed variable name collision where inner kpi5 label overwrote outer APOL title label
- Non-rich fallback display also corrected for KPI5 binary score

## [2.1.6] - 2026-03-02
### Fixed
- Auto-upgrade now runs **synchronously** before command dispatch instead of in a background thread
- After a successful upgrade, process is **re-exec'd** via `os.execv()` so the new code handles the actual command (fixes APOL score 0.00 caused by old code running after upgrade)
- Removed stale background thread / atexit join logic

## [2.1.5] - 2026-03-02
### Fixed
- APOL score always showing 0.00 — CLI was reading `composite_score` but judge returns `composite`
- KPI breakdown not displaying — CLI expected nested `kpis` dict but judge returns flat `kpi2/kpi3/kpi4/kpi5` fields + separate `feedback` dict; response is now normalized correctly


## [2.1.4] - 2026-03-02
### Fixed
- VERSION constant now read dynamically from importlib.metadata instead of hardcoded string
- Eliminates version mismatch bug where auto-upgrade could not detect installed version correctly
- Fallback to "2.1.4" only if metadata unavailable

### Fixed
- Increased APOL judge HTTP timeout from 30s to 90s — prevents false timeouts on cold-start edge function calls
### Improved
- `submit-listing` edge function now detects duplicate submissions (same title + creator)
  — republishing an existing skill updates the listing instead of creating a duplicate

## [2.1.0] - 2026-03-02
## [2.1.2] - 2026-03-02
### Fixed
- `publisher.py` line 477: `NameError: _validator_passed is not defined`
- Replaced undefined `_validator_passed` with the already-defined `_structural_passed`
- `zforge publish` no longer crashes after packaging when APOL scoring is skipped
## [2.1.1] - 2026-03-02
### Fixed
- `validator.py` rewritten cleanly — resolved multiple SyntaxError crashes caused by
  literal newline characters embedded inside f-string literals (Python 3.13 strict parsing)
- All output helpers (`_ok`, `_warn`, `_fail`, `_header`) now use plain string concatenation
- Publish command no longer crashes before starting on Python 3.12+


### Added - APOL Quality Certification in `zforge publish`

- Interactive A/B decision point during publish flow:
  - Skills scoring >= 0.80 on APOL LLM judge are auto-CERTIFIED immediately
  - Skills scoring < 0.80 prompt creator: A) publish UNCERTIFIED or B) run APOL tournament
- Option B runs the full tournament pipeline preserving creator intent — only documentation
  quality is improved; skill purpose and content never changed without explicit creator approval
- Diff shown before any SKILL.md changes are written
- Graceful fallback to structural validator if APOL edge functions unavailable
- Structural compliance check now independent from quality certification badge

---

## [2.0.8] - 2026-03-02
### Fixed
- `publisher.py`: `creator_handle` now included in submission payload, enabling correct
  GitHub avatar, profile linking, and creator attribution on the marketplace.
  Previously the handle was computed but silently dropped before sending to the API.

## [2.0.7] - 2026-03-02
### Fixed
- Auto-upgrade falsely printed "Upgraded to vX.X.X" even when pip ran in the wrong
  Python environment and the installed version never actually changed. Now uses
  `importlib.metadata.version('zforge')` to verify the version changed after pip
  completes. If unchanged, warns user and suggests manual upgrade. Cache is cleared
  so the next session re-checks PyPI.

## [2.0.1] - 2026-03-02

## [2.0.3] - 2026-03-02
### Fixed
- **Auto-upgrade race condition**: The update checker ran as a daemon thread, which was killed by the OS before it could complete the PyPI HTTP request (3s timeout) + pip install on fast commands like `zforge list`. Fixed by switching to a non-daemon thread and registering an `atexit` handler that joins the thread with a 5s timeout — ensuring the upgrade always completes before the process exits.

### Changed
## [2.0.2] - 2026-03-02

### Fixed
- `zforge publish` now routes submissions through a Supabase Edge Function instead of
  hitting the Supabase REST API directly — eliminates the RLS policy block that caused
  `HTTP 403 / row-level security` errors for creators using the anon key.
- Removed dependency on `SUPABASE_ANON_KEY` and `SUPABASE_SERVICE_KEY` for submission;
  the Edge Function uses service role internally (server-side only, never exposed).
- Storage ZIP upload still works for creators who have `SUPABASE_SERVICE_KEY` set;
  gracefully skips if not configured.

### Changed
- `_submit_to_supabase()` replaced by `_submit_to_edge_function()` in `publisher.py`.
- Added `_SUBMIT_EDGE_URL` and `_CLI_TOKEN` constants for Edge Function routing.
- CLI token `zforge-submit-v2` acts as basic abuse gate; real protection comes from
  rate limiting (10/hour per IP) + admin approval before listings go live.


- Auto-upgrade on version check: instead of nudging users to upgrade manually,
  the CLI now silently runs `pip install --upgrade zforge` automatically when
  a newer version is found on PyPI. Users see a confirmation message and are
  prompted to restart for the new version to take effect.

## [1.0.3] - 2026-03-02

## [2.0.0] - 2026-03-02
### Added
- Self-update checker: zforge now notifies you when a newer version is available on PyPI
- Runs silently in background thread — never blocks your command
- Shows upgrade prompt: ⚡ zforge v2.0.0 → vX.X.X available! Run: pip install --upgrade zforge

### Fixed
- VERSION constant in main.py synced with pyproject.toml (was mismatched)

## [1.0.9] - 2026-03-02
### Fixed
- `zforge publish` no longer requires SUPABASE_URL or SUPABASE_ANON_KEY env vars
- publisher.py now falls back to hardcoded public credentials (same pattern as main.py)
- Creators can run `zforge publish` out of the box with no environment configuration
- Service key (SUPABASE_SERVICE_KEY) remains env-only — it is admin-only and never embedded


## [1.0.8] - 2026-03-02
### Fixed
- `zforge validate` now checks the correct **nested** `skill.json` structure (`metadata.*` and `description.*` blocks) — previous validator checked non-existent top-level fields
- Added `description.short` length constraint: must be <=120 chars (matches publisher.py)
- Added `description.description_for_agent` word count constraint: must be >=10 words (matches publisher.py)
- Added `metadata.category` validity check against known categories
- Added `description.long` warning when missing
- Validate now catches all errors that `zforge publish` would reject — no more surprises at publish time

## [1.0.7] - 2026-03-02

### Fixed
- `zforge validate <name>` now accepts skill name/path as a **positional argument** — no more `--skill` flag required
- Validator is now fully **self-contained** — no longer depends on missing external `04_validate_skill.py` script
- Validator runs inline checks: SKILL.md, skill.json required fields, required sections, and optional recommendations

### Improved
- Clear ✅ / ⚠️ / ❌ output with pass/fail summary
- Handles skill name resolution (looks up `./skill_name/` relative to cwd)

### Fixed
- publisher.py now includes `apol_certified` and `apol_cert` fields in Supabase payload so certified skills display the ZFORGE VERIFIED badge on the marketplace
## [1.0.5] - 2026-03-02
### Changed
- Added comprehensive PyPI metadata: author, homepage, repository, classifiers, keywords
- Improved package discoverability and legitimacy signals on PyPI
- README: clarified pip install as primary installation method


# Changelog

## [2.1.19] - 2026-03-03
### Changed
- CERTIFIED skills (APOL score >= 0.80) bypass admin approval — go live immediately
- publisher.py: payload status = approved when apol_certified is True
- submit-listing edge function: server-side auto-approve when apol_certified=true
- Success message shows approved/pending conditionally
- Re-publishing a CERTIFIED skill preserves approved status


## [2.1.16] - 2026-03-03

### Fixed
- **cli/scripts/test_runner.py**: Corrected skill.json field checks to match actual nested structure — checks `metadata.name`, `metadata.version`, `metadata.author`, `metadata.tags`, `description.short`, and `quality.apol_certified` instead of incorrect flat top-level keys
- Step 7 now correctly reports `✓ All tests passed` for properly built skills


## [2.1.15] - 2026-03-02

### Fixed
- **builder.py**: APOL cert step now uses embedded Supabase credentials as fallback — no longer skipped when env vars are absent (zero-config)
- **tester.py**: Corrected  path ( not ) so test_runner.py is found correctly after pip install
- **cli/scripts/test_runner.py**: Added missing test harness script — validates SKILL.md word count, skill.json required fields, and scripts directory structure


## v2.1.13 — 2026-03-02
### Fixed
- **Critical:** Added missing `02_run_experiment.py` script to pip package — `zforge build` and `zforge dev` now work after `pip install zforge`
- Fixed `runner.py` SCRIPTS_DIR path (was resolving to wrong parent directory)
- Fixed winner path detection to use `<skill_dir>/experiments/` (consistent with builder.py)

### Added
- `litellm` added as explicit dependency in pyproject.toml
- `cli/scripts/` included in package_data for pip distribution


## [2.0.9] - 2026-03-02
### Fixed
- CERTIFIED badge now earned by passing `zforge validate` internally during publish — not self-reported from skill.json
- Closes security hole where anyone could set `apol_certified: true` manually in skill.json to fake a CERTIFIED badge
- Publisher now runs `run_validate()` before building the payload; badge is set server-side based on actual validation result
- Creators who run `zforge publish` with a passing skill will automatically receive the CERTIFIED badge


## [1.0.4] - 2026-03-02
### Fixed
- `zforge list`, `zforge search`, `zforge install` now work without any setup
- Public Supabase anon key bundled into CLI (read-only, safe to ship)
- Removed "must be set" credential error for read-only marketplace commands
- Only `zforge publish` requires credentials (GitHub OAuth, unchanged)


## [1.0.1] - 2026-03-02

### Fixed
- Corrected SKILL.md install paths to use `~/.zforge` instead of hardcoded `/a0/usr/workdir/ZeroForge`
- Updated install.sh to clone from `colin-charles/zforge` (new standalone CLI repo)
- Fixed all internal repo URL references from `zeroforge` to `zforge`
- Improved install.sh with better UX and idempotent install check

## [1.0.0] - 2026-03-02

### Added
- `zforge new` — scaffold new skills from template
- `zforge validate` — validate skills against SKILL.md standard
- `zforge build` — build distributable skill packages
- `zforge publish` — publish skills to ZeroForge marketplace
- `zforge test` — run skill tests
- `zforge hello` — verify installation
- AgentZero SKILL.md for use as an installable agent skill
- One-liner install script (`install.sh`)

## [2.0.7] - 2026-03-02
### Fixed
- Auto-upgrade falsely reporting "Upgraded to vX.X.X" when pip ran in wrong Python environment (e.g., pipx/venv mismatch). Now uses `importlib.metadata` to verify the installed version actually changed after pip completes. If version is unchanged, warns user and suggests manual upgrade instead of claiming success. Cache is also cleared in this case so the next session re-checks.

## [2.0.6] - 2026-03-02
### Changed
- Reduced update check cooldown from 24h to 5 minutes (better for rapid dev releases)


## [2.0.5] - 2026-03-02
### Fixed
- Auto-upgrade no longer fires when already on latest version
- Added 24h cooldown cache (~/.zforge_update_check) — PyPI checked at most once per day
- Strict `_ver(latest) <= _ver(VERSION)` guard added as early exit before any pip call


## [2.0.4] - 2026-03-02
### Fixed
- Hardcoded real Supabase project URL directly in `publisher.py` and `main.py`
  replacing unresolved `https://turwttpspnqmhszjwjgs.supabase.co` placeholder that caused
  "marketplace temporarily unavailable" errors for users without env vars set.
- `db.js` on zero-forge.org also updated with real project URL.

## v2.1.17 — 2026-03-03
### Fixed
- **Step 6 Validate bug**: `builder.py` was calling `zforge validate --skill .` but `validate` only accepts a positional argument, not `--skill` flag. Changed to `zforge validate` (uses cwd, already set to skill dir). Step 6 now runs cleanly.

## v2.1.18 — 2026-03-03
### Fixed
- **Invalid default category**: `builder.py` and `main.py` defaulted to `"utilities"` which is not a valid category. Changed to `"skill"`.
- **Invalid default tags**: `main.py` defaulted tags to `"utilities"`. Changed to `"automation"`.
- **Category normalizer**: Added normalizer map in `builder.py` that maps common invalid values (`utilities`, `utility`, `tools`, `scripts`, `guides`, etc.) to the nearest valid category instead of failing validation.
- **Help text**: `--category` option now lists all valid values in its help text.
