from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import glob
from typing import Optional


@dataclass
class ToolInfo:
    name: str
    path: Optional[str]
    ok: bool
    details: str = ""


ALLOWED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
PDF_EXT = ".pdf"


def which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def exists_file(path: str) -> bool:
    return bool(path) and os.path.isfile(path)


def resolve_tool_path(env_value: str | None, fallback_cmd: str) -> Optional[str]:
    if env_value and exists_file(env_value):
        return env_value
    return which(fallback_cmd)


def get_ext(path: str) -> str:
    return Path(path).suffix.lower()


def is_pdf(path: str) -> bool:
    return get_ext(path) == PDF_EXT


def is_image(path: str) -> bool:
    return get_ext(path) in ALLOWED_IMAGE_EXTS


def file_size_bytes(path: str) -> int:
    return os.path.getsize(path)


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def make_temp_dir(base_dir: str = "outputs") -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir = os.path.join(base_dir, f"tmp_{ts}")
    return ensure_dir(tmp_dir)


def copy_to(src: str, dst_dir: str, dst_name: str) -> str:
    ensure_dir(dst_dir)
    dst_path = os.path.join(dst_dir, dst_name)
    shutil.copy2(src, dst_path)
    return dst_path

def get_latest_summary(base_dir="outputs"):
    # Find all 'final_summary.md' files within any subdirectory of base_dir
    search_path = os.path.join(base_dir, "**/final_summary.md")
    files = glob.glob(search_path, recursive=True)
    
    if not files:
        return None
        
    # Sort files by creation time to get the absolute newest one
    latest_file = max(files, key=os.path.getctime)
    return latest_file
