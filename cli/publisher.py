
"""zforge publish -- validate, package, upload, and publish a skill to ZeroForge marketplace."""
from __future__ import annotations

import json
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    from pydantic import BaseModel, validator
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── Public read-only Supabase credentials (anon key — safe to embed) ─────────
# Creators don't need to configure env vars to publish — these are fallbacks.
_PUBLIC_SUPABASE_URL  = "https://turwttpspnqmhszjwjgs.supabase.co"
_PUBLIC_SUPABASE_ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR1cnd0dHBzcG5xbWhzemp3amdzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIyMDM3NzAsImV4cCI6MjA4Nzc3OTc3MH0.fBajcHIJZs1lYwfEJRtnHvZdjqZ2u7YGIuPnhyAg85g"

# ── Edge Function endpoint (routes submissions through service role — bypasses RLS)
_SUBMIT_EDGE_URL = "https://turwttpspnqmhszjwjgs.supabase.co/functions/v1/submit-listing"
_CLI_TOKEN       = "zforge-submit-v2"  # public abuse-gate token, not a secret


try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    from rich.rule import Rule
    from rich.syntax import Syntax
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print(msg: str, style: str = ""):
    if HAS_RICH:
        console.print(msg, style=style if style else None)
    else:
        import re
        plain = re.sub(r'\[/?[a-zA-Z_ ]+\]', '', msg)
        print(plain)


def _rule(title: str):
    if HAS_RICH:
        console.print(Rule(title))
    else:
        print(f"\n{'-' * 60} {title} {'-' * 60}")


def load_env():
    """Load env from secrets.env (Agent Zero secrets store) or .env fallback."""
    candidates = [
        Path('/a0/usr/secrets.env'),          # Agent Zero secrets store (preferred)
        Path('/a0/usr/workdir/ZeroForge/.env'), # project .env fallback
        Path.home() / '.env',
    ]
    for env_path in candidates:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())
            return env_path
    return None


def _is_placeholder(val: str) -> bool:
    if not val:
        return True
    placeholders = ['your-service-role-key-here', 'your-anon-key-here',
                    'placeholder', 'change-me', 'TODO', '<']
    return any(p in val for p in placeholders)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

if HAS_PYDANTIC:
    class SkillManifest(BaseModel):
        class Metadata(BaseModel):
            name: str
            slug: str
            version: str
            author: str
            author_url: str = ""
            license: str
            category: str
            tags: List[str]
            repository: Optional[str] = None

        class Description(BaseModel):
            short: str
            long: str
            description_for_agent: str

            @validator('short')
            def check_short(cls, v):
                if len(v) > 120:
                    raise ValueError(f'short description must be <=120 chars (got {len(v)})')
                return v

            @validator('description_for_agent')
            def check_agent_desc(cls, v):
                if len(v.split()) < 10:
                    raise ValueError(f'description_for_agent must be >=10 words (got {len(v.split())})')
                return v

        class Quality(BaseModel):
            apol_certified: bool
            apol_cert_id: Optional[str] = None
            apol_composite_score: Optional[float] = None

        metadata: Metadata
        description: Description
        quality: Quality

else:
    class SkillManifest:  # type: ignore
        def __init__(self, data: dict):
            self._data = data

        @classmethod
        def model_validate(cls, data: dict):
            inst = cls(data)
            meta = data.get('metadata', {})
            for field in ('name', 'slug', 'version', 'author', 'license', 'category', 'tags'):
                if field not in meta:
                    raise ValueError(f'metadata.{field} is required')
            desc = data.get('description', {})
            short = desc.get('short', '')  
            if len(short) > 120:
                raise ValueError('short description must be <=120 chars')
            agent_desc = desc.get('description_for_agent', '')  
            if len(agent_desc.split()) < 10:
                raise ValueError('description_for_agent must be >=10 words')
            return inst

        def __getattr__(self, name):
            return self._data.get(name, {})


# ---------------------------------------------------------------------------
# Packaging
# ---------------------------------------------------------------------------

EXCLUDE_PATTERNS = {
    '.git', '__pycache__', '.egg-info', 'venv', 'experiments',
    'test_skill_cli', '.DS_Store',
}


def _should_exclude(rel_path: str) -> bool:
    parts = Path(rel_path).parts
    for part in parts:
        if part in EXCLUDE_PATTERNS:
            return True
        for pat in EXCLUDE_PATTERNS:
            if part.endswith(pat):
                return True
    return False


def package_skill(skill_dir: Path) -> Path:
    """ZIP the skill directory, return path to ZIP file."""
    skill_name = skill_dir.resolve().name
    zip_path = skill_dir.parent / f"{skill_name}.zip"
    file_count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fpath in sorted(skill_dir.rglob('*')):
            if not fpath.is_file():
                continue
            rel = fpath.relative_to(skill_dir)
            rel_str = str(rel)
            if _should_exclude(rel_str):
                continue
            zf.write(fpath, arcname=f"{skill_name}/{rel_str}")
            file_count += 1
    _print(f"  [cyan]Packaged {file_count} files -> {zip_path.name}[/cyan]")
    return zip_path


# ---------------------------------------------------------------------------
# Supabase Storage upload
# ---------------------------------------------------------------------------

def upload_to_storage(zip_path: Path, skill_name: str, service_key: str, supabase_url: str) -> Optional[str]:
    """
    Upload zip to Supabase Storage 'skills' bucket.
    Returns the public URL or None on failure.
    """
    if not HAS_REQUESTS:
        _print("  [yellow]requests not installed — skipping storage upload[/yellow]")
        return None

    if not service_key or _is_placeholder(service_key):
        _print("  [yellow]SUPABASE_SERVICE_KEY not set — skipping storage upload[/yellow]")
        return None

    storage_path = f"{skill_name}/{zip_path.name}"
    upload_url = f"{supabase_url}/storage/v1/object/skills/{storage_path}"

    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/zip",
        "x-upsert": "true",  # overwrite if exists
    }

    _print(f"  Uploading {zip_path.name} to Supabase Storage...")
    try:
        with open(zip_path, 'rb') as f:
            resp = requests.post(upload_url, headers=headers, data=f, timeout=120)

        if resp.status_code in (200, 201):
            project_ref = supabase_url.split('//')[1].split('.')[0]
            public_url = f"{supabase_url}/storage/v1/object/public/skills/{storage_path}"
            _print(f"  [green]Uploaded -> {public_url}[/green]")
            return public_url
        else:
            _print(f"  [yellow]Storage upload failed [{resp.status_code}]: {resp.text[:200]}[/yellow]")
            _print("  [dim]Falling back to repo URL only[/dim]")
            return None
    except Exception as e:
        _print(f"  [yellow]Storage upload error: {e}[/yellow]")
        return None


# ---------------------------------------------------------------------------
# APOL cert loader
# ---------------------------------------------------------------------------

def _load_apol_cert(skill_dir: Path) -> dict:
    exp_dir = skill_dir / 'experiments'
    if not exp_dir.exists():
        return {}
    meta_files = sorted(exp_dir.rglob('experiment_meta.json'))
    if not meta_files:
        return {}
    try:
        return json.loads(meta_files[-1].read_text())
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Supabase REST submission
# ---------------------------------------------------------------------------

# SUPABASE_REST_URL no longer used — submissions route through Edge Function
SUPABASE_DASHBOARD = "https://supabase.com/dashboard/project/turwttpspnqmhszjwjgs/editor"

RLS_FIX_SQL = """
CREATE POLICY IF NOT EXISTS "Public submit listings"
  ON public.listings FOR INSERT WITH CHECK (true);
""".strip()



def _submit_to_edge_function(payload: dict) -> dict:
    """Submit listing via Supabase Edge Function (service role — bypasses RLS)."""
    if not HAS_REQUESTS:
        raise RuntimeError("pip install requests")

    # Allow override via env var for self-hosting
    edge_url = os.environ.get("ZFORGE_SUBMIT_URL") or _SUBMIT_EDGE_URL
    if not edge_url:
        raise RuntimeError(
            "ZFORGE_SUBMIT_URL not set and public fallback is missing — contact support"
        )

    headers = {
        "Content-Type": "application/json",
        "x-zforge-token": _CLI_TOKEN,
    }

    _print("  Connecting to ZeroForge marketplace ...")
    try:
        resp = requests.post(edge_url, headers=headers, json=payload, timeout=30)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Network error — check your internet connection")
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out — ZeroForge may be temporarily unavailable")

    if resp.status_code == 201:
        return resp.json()

    try:
        err = resp.json()
        msg = err.get("error") or err.get("message") or resp.text[:300]
    except Exception:
        msg = resp.text[:300]

    if resp.status_code == 401:
        raise RuntimeError(
            "CLI token rejected — please upgrade: pip install --upgrade zforge"
        )
    if resp.status_code == 422:
        raise RuntimeError(f"Validation failed: {msg}")
    if resp.status_code == 429:
        raise RuntimeError("Rate limit exceeded — max 10 submissions per hour")
    if resp.status_code == 503:
        raise RuntimeError(
            "ZeroForge marketplace is temporarily unavailable — try again later"
        )
    raise RuntimeError(f"Submission failed [{resp.status_code}]: {msg}")


def publish_skill(skill_dir_arg: Path, dry_run: bool = False, source_repo: str = ""):
    skill_dir = Path(skill_dir_arg).resolve()
    skill_name = skill_dir.name

    _rule(f"zforge publish -- {skill_name}")

    # 1. Load .env
    env_file = load_env()
    if env_file:
        _print(f"  [green]Loaded env from {env_file}[/green]")

    supabase_url = (os.environ.get('SUPABASE_URL') or _PUBLIC_SUPABASE_URL).rstrip('/')

    # 2. Read & validate skill.json
    manifest_path = skill_dir / 'skill.json'
    if not manifest_path.exists():
        _print(f"  [bold red]skill.json not found at {manifest_path}[/bold red]")
        sys.exit(1)
    try:
        raw = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        _print(f"  [bold red]skill.json invalid JSON: {e}[/bold red]")
        sys.exit(1)

    _print("  Validating skill.json ...")
    try:
        if HAS_PYDANTIC:
            manifest = SkillManifest.model_validate(raw)
            meta = manifest.metadata
            desc = manifest.description
            quality = manifest.quality
        else:
            manifest = SkillManifest.model_validate(raw)
            meta_raw = raw.get('metadata', {})
            desc_raw = raw.get('description', {})
            quality_raw = raw.get('quality', {})
            class _NS: pass
            meta = _NS()
            meta.name = meta_raw.get('name', '')  
            meta.slug = meta_raw.get('slug', '')  
            meta.version = meta_raw.get('version', '')  
            meta.author = meta_raw.get('author', '')  
            meta.author_url = meta_raw.get('author_url', '')  
            meta.license = meta_raw.get('license', '')  
            meta.category = meta_raw.get('category', '')  
            meta.tags = meta_raw.get('tags', [])
            meta.repository = meta_raw.get('repository', None)
            desc = _NS()
            desc.short = desc_raw.get('short', '')  
            desc.description_for_agent = desc_raw.get('description_for_agent', '')  
            quality = _NS()
            quality.apol_certified = quality_raw.get('apol_certified', False)
            quality.apol_cert_id = quality_raw.get('apol_cert_id', None)
            quality.apol_composite_score = quality_raw.get('apol_composite_score', None)
    except Exception as e:
        _print(f"  [bold red]Validation failed: {e}[/bold red]")
        sys.exit(1)
    _print("  [green]skill.json validation passed[/green]")

    # 3. Load APOL cert
    cert = _load_apol_cert(skill_dir)
    cert_id = getattr(quality, 'apol_cert_id', None) or cert.get('cert_id')
    apol_score = getattr(quality, 'apol_composite_score', None) or cert.get('composite_score')

    # 4. Category mapping
    CATEGORY_MAP = {
        "dev-tools": "skill", "development": "skill", "tool": "skill",
        "guide": "guide", "tutorial": "guide", "howto": "guide",
        "template": "template", "scaffold": "template",
        "script": "script", "automation": "script",
        "course": "course", "training": "course",
        "consulting": "consulting", "service": "consulting",
    }
    VALID_CATEGORIES = {"skill", "guide", "template", "script", "course", "consulting"}
    raw_cat = (meta.category or "").lower().strip()
    mapped_cat = CATEGORY_MAP.get(raw_cat, raw_cat if raw_cat in VALID_CATEGORIES else "skill")
    tags_list = meta.tags if isinstance(meta.tags, list) else [str(meta.tags)]

    # 5. Resolve GitHub handle
    def _extract_github_handle(author_url: str, author: str) -> str:
        if author_url and 'github.com' in author_url:
            return author_url.rstrip('/').split('github.com/')[-1].split('/')[0]
        if author and ' ' not in author.strip():
            return author.strip()
        return ''
    creator_handle = _extract_github_handle(meta.author_url, meta.author)

    # 6. Resolve source_url (GitHub repo for transparency — optional)
    resolved_source = source_repo or getattr(meta, 'repository', None) or ''

    # 7. Package
    _print("  Packaging skill ...")
    zip_path = package_skill(skill_dir)
    zip_size_kb = zip_path.stat().st_size // 1024

    # 8. Upload to Supabase Storage (always attempt, even in dry_run preview)
    storage_url = None
    if not dry_run:
        service_key = os.environ.get("SUPABASE_SERVICE_KEY", "")  # optional: enables ZIP storage upload
        storage_url = upload_to_storage(zip_path, skill_name, service_key, supabase_url)
    else:
        _print("  [dim]DRY RUN: storage upload skipped[/dim]")

    # 9. Build payload
    payload = {
        "title": meta.name,
        "description": desc.short,
        "creator_name": meta.author,
        "creator_handle": creator_handle or "",
        "creator_email": "",
        "url": storage_url or resolved_source or "",   # primary install URL
        "storage_url": storage_url or "",             # Supabase Storage zip
        "source_url": resolved_source or "",          # GitHub source (optional)
        "category": mapped_cat,
        "tags": tags_list,
        "price": "free",
        "status": "pending",
        "apol_certified": bool(getattr(quality, 'apol_certified', False)),
        "apol_cert": {
            "apol_composite_score": apol_score,
            "apol_cert_id": cert_id,
        } if getattr(quality, 'apol_certified', False) else None,
    }

    # 10. Summary panel
    if HAS_RICH:
        summary = Table(box=box.SIMPLE, show_header=False)
        summary.add_column("Field", style="dim")
        summary.add_column("Value", style="bold")
        summary.add_row("Skill", meta.name)
        summary.add_row("Version", meta.version)
        summary.add_row("Author", meta.author)
        summary.add_row("GitHub", creator_handle or "(not set)")
        summary.add_row("Category", mapped_cat)
        summary.add_row("Tags", ", ".join(tags_list))
        summary.add_row("APOL Score", str(round(apol_score, 4)) if apol_score else "(none)")
        summary.add_row("ZIP", f"{zip_path.name} ({zip_size_kb}KB)")
        summary.add_row("Storage URL", storage_url or "(pending upload)")
        summary.add_row("Source URL", resolved_source or "(none — creator keeps code private)")
        console.print(Panel(summary, title="[bold cyan]Publish Summary[/bold cyan]", border_style="cyan"))
    else:
        for k, v in payload.items():
            print(f"  {k}: {v}")

    if dry_run:
        _print("  [bold yellow]DRY RUN -- skipping Supabase submission[/bold yellow]")
        _print("  [green]Remove --dry-run to publish for real.[/green]")
        return

    # 11. Submit listing to Supabase
    _print("  Submitting to ZeroForge marketplace ...")
    try:
        result = _submit_to_edge_function(payload)
    except RuntimeError as e:
        _print(f"  [bold red]Submission failed: {e}[/bold red]")
        sys.exit(1)

    listing_id = result.get('id', 'unknown')
    listing_slug = result.get('slug', getattr(meta, 'slug', skill_name))

    # 12. Save record
    record = {
        "submitted_at": datetime.utcnow().isoformat(),
        "listing_id": listing_id,
        "storage_url": storage_url,
        "source_url": resolved_source,
        "payload": payload,
        "response": result,
    }
    record_path = skill_dir / 'publish_record.json'
    record_path.write_text(json.dumps(record, indent=2))

    if HAS_RICH:
        lines = (
            "[bold green]Listing created![/bold green]\n\n"
            f"  [bold]ID:[/bold]          {listing_id}\n"
            f"  [bold]Status:[/bold]      [yellow]pending[/yellow]\n"
            f"  [bold]Storage URL:[/bold] {storage_url or '(none)'}\n"
            f"  [bold]Source URL:[/bold]  {resolved_source or '(private)'}\n"
            f"  [bold]Listing:[/bold]     https://zero-forge.org/listing/?id={listing_id}\n"
            f"  [bold]Record:[/bold]      {record_path.name}\n"
        )
        console.print(Panel(
            lines,
            title="[bold green]Published[/bold green]",
            border_style="green",
        ))
    else:
        print(f"\nPublished! ID: {listing_id}")
        print(f"  https://zero-forge.org/listing/?id={listing_id}")
