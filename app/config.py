from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv
@dataclass(frozen=True)
class Settings:
   tesseract_cmd: str | None
   poppler_bin: str | None
def load_settings() -> Settings:
    """
    Loads .env if present (user will create .env from .env.example).
    Keeps Phase 0 simple: just read tool paths.
    """
    load_dotenv(override=False)

    tesseract_cmd = os.getenv("TESSERACT_CMD") or None
    poppler_bin = os.getenv("POPPLER_BIN") or None

    # Normalize empty strings to None
    if tesseract_cmd is not None and not tesseract_cmd.strip():
        tesseract_cmd = None
    if poppler_bin is not None and not poppler_bin.strip():
        poppler_bin = None

    return Settings(tesseract_cmd=tesseract_cmd, poppler_bin=poppler_bin)