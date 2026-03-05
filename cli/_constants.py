"""Shared constants for the zforge CLI.

Every other module imports from here — no constant should be
defined in more than one place.
"""
import os

# ── Public read-only Supabase credentials (anon key — safe to embed) ─────────
# Creators don’t need to configure env vars to publish — these are fallbacks.
_PUBLIC_SUPABASE_URL  = "https://turwttpspnqmhszjwjgs.supabase.co"
_PUBLIC_SUPABASE_ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR1cnd0dHBzcG5xbWhzemp3amdzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIyMDM3NzAsImV4cCI6MjA4Nzc3OTc3MH0.fBajcHIJZs1lYwfEJRtnHvZdjqZ2u7YGIuPnhyAg85g"
_PUBLIC_SUPABASE_SVC  = ""  # service key NEVER embedded in public package

# ── Derived Edge Function URLs ───────────────────────────────────────────────
_SUBMIT_EDGE_URL = f"{_PUBLIC_SUPABASE_URL}/functions/v1/submit-listing"
_UPLOAD_EDGE_URL = f"{_PUBLIC_SUPABASE_URL}/functions/v1/upload-skill-zip"

# ── Abuse-gate token (not a secret — public, rotatable) ─────────────────────
_CLI_TOKEN = "zforge-submit-v2"

# ── APOL certification threshold ─────────────────────────────────────────────
CERTIFIED_THRESHOLD = 0.80

# ── Marketplace categories ───────────────────────────────────────────────────
VALID_CATEGORIES = {"skill", "guide", "template", "script", "course", "consulting"}

CATEGORY_MAP = {
    "skills": "skill",
    "guides": "guide",
    "templates": "template",
    "scripts": "script",
    "courses": "course",
}


# ── Helper ───────────────────────────────────────────────────────────────────
def get_supabase_url() -> str:
    """Return the Supabase project URL, preferring env var over embedded."""
    return (os.environ.get("SUPABASE_URL") or _PUBLIC_SUPABASE_URL).rstrip("/")
