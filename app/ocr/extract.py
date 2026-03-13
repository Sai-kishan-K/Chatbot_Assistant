from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from PIL import Image
import pytesseract

from app.config import load_settings
from app.utils.logger import get_logger

log = get_logger()


@dataclass(frozen=True)
class OCRResult:
    text: str
    page_texts: List[str]
    warnings: str


def _configure_tesseract() -> Optional[str]:
    """
    Configure pytesseract to use explicit TESSERACT_CMD if provided.
    Returns the resolved tesseract_cmd used (or None).
    """
    settings = load_settings()
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        return settings.tesseract_cmd
    return None


def ocr_images(image_paths: List[str]) -> OCRResult:
    """
    OCR each image and combine text with clear page separators.
    MVP rules: English only, printed text only.
    """
    used_cmd = _configure_tesseract()
    if used_cmd:
        log.info(f"Using Tesseract from: {used_cmd}")

    page_texts: List[str] = []
    warnings = []

    for idx, path in enumerate(image_paths, start=1):
        try:
            img = Image.open(path)
            # Basic, stable OCR config for printed English:
            # --oem 3 = default engine, --psm 6 = assume a block of text
            txt = pytesseract.image_to_string(img, lang="eng", config="--oem 3 --psm 6")
            txt = txt or ""
        except Exception as e:
            txt = ""
            warnings.append(f"Page {idx}: OCR failed ({e})")

        page_texts.append(txt)

    combined_parts: List[str] = []
    for i, t in enumerate(page_texts, start=1):
        combined_parts.append(f"\n\n----- PAGE {i} -----\n\n")
        combined_parts.append(t)

    combined = "".join(combined_parts).strip()
    warn_text = "; ".join(warnings) if warnings else ""

    return OCRResult(text=combined, page_texts=page_texts, warnings=warn_text)
