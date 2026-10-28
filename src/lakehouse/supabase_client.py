"""
FoodFlow Cloud Lakehouse — Supabase Storage Client
File: src/lakehouse/supabase_client.py

Description:
    Provides authenticated connection and helper utilities for interacting
    with Supabase Storage buckets (Bronze, Silver, Gold).
"""

import io
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import Client, create_client

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

BUCKETS = {
    "bronze": "foodflow-bronze",
    "silver": "foodflow-silver",
    "gold": "foodflow-gold",
}


def get_storage_client() -> Client:
    """Initialize and return authenticated Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env file."
        )
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_bytes(bucket_name: str, file_bytes: bytes, remote_path: str, content_type: str = "application/octet-stream") -> str:
    """Upload raw bytes to a target Supabase Storage bucket."""
    client = get_storage_client()
    res = client.storage.from_(bucket_name).upload(
        path=remote_path,
        file=file_bytes,
        file_options={"upsert": "true", "content-type": content_type},
    )
    return remote_path


def download_bytes(bucket_name: str, remote_path: str) -> bytes:
    """Download file bytes from a target Supabase Storage bucket."""
    client = get_storage_client()
    return client.storage.from_(bucket_name).download(remote_path)


def list_bucket_files(bucket_name: str, prefix: str = "") -> list:
    """List objects in a target Supabase bucket."""
    client = get_storage_client()
    return client.storage.from_(bucket_name).list(prefix)
