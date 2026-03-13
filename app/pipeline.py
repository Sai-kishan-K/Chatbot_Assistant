from __future__ import annotations

import os
from typing import List, Optional

from pdf2image import convert_from_path

from app.config import load_settings
from app.utils.files import (
    ensure_dir,
    file_size_bytes,
    is_image,
    is_pdf,
    make_temp_dir,
    copy_to,
)

from app.ocr.web_extract import extract_text_from_url
from app.ocr.extract import ocr_images
from app.cleaning.clean import clean_ocr_text
from app.llm.summarize import summarize_documentation

from app.utils.logger import get_logger

log = get_logger()

MAX_FILE_MB = 5


class InputValidationError(ValueError):
    pass


def validate_input_file(path: str) -> None:
    if not path or not os.path.isfile(path):
        raise InputValidationError(f"Input file not found: {path}")

    size_mb = file_size_bytes(path) / (1024 * 1024)
    if size_mb > MAX_FILE_MB:
        raise InputValidationError(f"File too large: {size_mb:.2f} MB (max {MAX_FILE_MB} MB)")

    if not (is_pdf(path) or is_image(path)):
        raise InputValidationError("Unsupported file type. Use PDF or image (png/jpg/jpeg/tif/tiff).")


def load_document_images(input_path: str, max_pages: Optional[int] = None) -> tuple[str, List[str]]:
    """
    Phase 1 output:
      - tmp_dir: folder containing generated/copied images
      - image_paths: list of image paths in reading order
    """
    validate_input_file(input_path)

    if max_pages is not None and max_pages < 1:
        max_pages = 1

    tmp_dir = make_temp_dir(base_dir="outputs")
    ensure_dir(tmp_dir)

    # IMAGE input: copy into tmp as page_1
    if is_image(input_path):
        ext = os.path.splitext(input_path)[1].lower()
        out_path = copy_to(input_path, tmp_dir, f"page_1{ext}")
        log.info("Detected image input.")
        return tmp_dir, [out_path]

    # PDF input: convert all pages unless a limit was explicitly provided
    log.info("Detected PDF input. Converting pages to images...")
    settings = load_settings()
    poppler_bin = settings.poppler_bin  # may be None if tools are on PATH

    convert_kwargs = {
        "dpi": 300,
        "first_page": 1,
        "poppler_path": poppler_bin,
        "fmt": "png",
    }
    if max_pages is not None:
        convert_kwargs["last_page"] = max_pages

    pages = convert_from_path(input_path, **convert_kwargs)

    image_paths: List[str] = []
    for i, img in enumerate(pages, start=1):
        out_path = os.path.join(tmp_dir, f"page_{i}.png")
        img.save(out_path, "PNG")
        image_paths.append(out_path)

    return tmp_dir, image_paths

def run_pipeline(input_path: Optional[str] = None, url: Optional[str] = None, max_pages: Optional[int] = None) -> int:
    """
    Main Orchestrator: Handles either local files or URLs.
    """
    try:
        raw_text = ""

        # PATH A: Web Scraping
        if url:
            log.info(f"Starting Web Pipeline for: {url}")
            raw_text = extract_text_from_url(url)
        
        # PATH B: PDF/Image OCR
        elif input_path:
            log.info(f"Starting OCR Pipeline for: {input_path}")
            tmp_dir, image_paths = load_document_images(input_path, max_pages)
            ocr_result = ocr_images(image_paths)
            raw_text = ocr_result.text
        
        else:
            log.error("No input provided (path or url).")
            return 1

        if not raw_text:
            log.warning("No text extracted.")
            return 1

        # Phase 3: Cleaning (Unified for both sources)
        log.info("Phase 3: Cleaning text...")
        clean_result = clean_ocr_text(raw_text)
        
        print(f"\n--- CLEANED OUTPUT ---\n{clean_result.cleaned_text[:1000]}...")
        return 0

    except Exception as e:
        log.error(f"Pipeline failed: {e}")
        return 1
