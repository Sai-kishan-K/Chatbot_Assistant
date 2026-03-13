from __future__ import annotations

import argparse
import os
import subprocess
import sys

from app.cleaning.clean import clean_ocr_text
from app.ocr.extract import ocr_images
from app.ocr.web_extract import extract_text_from_url
from app.config import load_settings
from app.pipeline import load_document_images, InputValidationError
from app.utils.files import resolve_tool_path, ToolInfo, which
from app.utils.logger import get_logger

from app.llm.summarize import summarize_documentation

log = get_logger()


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out.strip()
    except Exception as e:
        return 1, f"ERROR running {cmd}: {e}"


def verify_env() -> int:
    settings = load_settings()

    tesseract_path = resolve_tool_path(settings.tesseract_cmd, "tesseract")
    tesseract_ok = bool(tesseract_path)

    poppler_bin = settings.poppler_bin
    pdftoppm_path = None
    pdfinfo_path = None

    if poppler_bin and os.path.isdir(poppler_bin):
        pdftoppm_path = os.path.join(poppler_bin, "pdftoppm.exe")
        pdfinfo_path = os.path.join(poppler_bin, "pdfinfo.exe")
    else:
        pdftoppm_path = which("pdftoppm")
        pdfinfo_path = which("pdfinfo")

    log.info(f"Python: {sys.version.split()[0]}")
    log.info(f"TESSERACT_CMD env: {settings.tesseract_cmd or '(not set)'}")
    log.info(f"POPPLER_BIN env: {settings.poppler_bin or '(not set)'}")

    log.info(f"Tesseract path: {tesseract_path or '(NOT FOUND)'}")
    log.info(f"pdftoppm path: {pdftoppm_path or '(NOT FOUND)'}")
    log.info(f"pdfinfo path: {pdfinfo_path or '(NOT FOUND)'}")

    if not tesseract_ok:
        log.error("Tesseract not found.")
        return 1
    if not (pdftoppm_path and pdfinfo_path):
        log.error("Poppler tools not found.")
        return 1

    log.info("ENV OK ✅ (Tesseract + Poppler detected)")
    return 0


def run_phase1(input_path: str, max_pages: int, do_ocr: bool, do_clean: bool) -> int:
    try:
        tmp_dir, images = load_document_images(input_path, max_pages=max_pages)
        log.info(f"Temp folder: {tmp_dir}")
        log.info(f"Pages/images loaded: {len(images)}")
        for p in images:
            log.info(f" - {p}")

        if not do_ocr:
            return 0

        # PHASE 2: OCR
        log.info("Starting OCR (Phase 2)...")
        result = ocr_images(images)

        out_txt = os.path.join(tmp_dir, "extracted_text.txt")
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write(result.text)

        log.info(f"OCR complete. Extracted characters: {len(result.text)}")
        log.info(f"Saved: {out_txt}")

        #PHASE 3:CLEANING

        if do_clean:
            log.info("Starting cleaning (Phase 3)...")
            cleaned = clean_ocr_text(result.text)

            out_clean = os.path.join(tmp_dir, "cleaned_text.txt")
            with open(out_clean, "w", encoding="utf-8") as f:
                f.write(cleaned.cleaned_text)

            log.info(f"Cleaning complete. Cleaned characters: {len(cleaned.cleaned_text)}")
            log.info(f"Saved: {out_clean}")

            if cleaned.removed_lines:
                log.info(f"Removed repeated header/footer lines: {cleaned.removed_lines}")


        if result.warnings:
            log.warning(f"OCR warnings: {result.warnings}")

        # small preview (first 300 chars)
        preview = result.text[:300].replace("\n", " ")
        log.info(f"Preview: {preview}{'...' if len(result.text) > 300 else ''}")

        return 0

    except InputValidationError as e:
        log.error(str(e))
        return 2
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        return 1

def run_web_phase(url: str, do_clean: bool, max_pages: int | None = None) -> int:
    try:
        from app.ocr.web_extract import get_all_doc_links, extract_text_from_url
        from app.utils.files import make_temp_dir, ensure_dir

        log.info(f"Crawling site: {url}")
        all_links = get_all_doc_links(url)
        if max_pages is not None:
            if max_pages < 1:
                max_pages = 1
            all_links = all_links[:max_pages]
        
        tmp_dir = make_temp_dir(base_dir="outputs")
        ensure_dir(tmp_dir)
        
        combined_raw_text = ""

        for i, link in enumerate(all_links):
            log.info(f"Processing ({i+1}/{len(all_links)}): {link}")
            page_text = extract_text_from_url(link)
            combined_raw_text += f"\n\n----- PAGE {i+1}: {link} -----\n\n" + page_text

        # Save Raw
        out_raw = os.path.join(tmp_dir, "web_raw_combined.txt")
        with open(out_raw, "w", encoding="utf-8") as f:
            f.write(combined_raw_text)

        if do_clean:
            log.info("Cleaning combined web text...")
            cleaned = clean_ocr_text(combined_raw_text)
            out_clean = os.path.join(tmp_dir, "web_cleaned_combined.txt")
            with open(out_clean, "w", encoding="utf-8") as f:
                f.write(cleaned.cleaned_text)
            log.info(f"Saved cleaned combined text to: {out_clean}")

            log.info("Phase 4: Sending cleaned text to Gemini...")
    
            # We use the cleaned text we just generated
            summary_text = summarize_documentation(cleaned.cleaned_text)
            
            # Save the Final Summary as a Markdown file in the same temp path
            out_summary = os.path.join(tmp_dir, "final_summary.md")
            with open(out_summary, "w", encoding="utf-8") as f:
                f.write(summary_text)
            
            log.info(f"Summary saved successfully in: {out_summary}")
            
            print("\n" + "="*30)
            print("FINAL SUMMARY PREVIEW")
            print("="*30)
            print(summary_text[:1000] + "...")

        return 0
    except Exception as e:
        log.error(f"Web Phase failed: {e}")
        return 1
    

def main() -> None:
    parser = argparse.ArgumentParser(prog="ocr-llm-mvp")

    parser.add_argument("--verify-env", action="store_true")
    parser.add_argument("--input", type=str, help="Path to input PDF/image")
    parser.add_argument("--url", type=str, help="URL to scrape")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages/links to process. Defaults to all discovered pages.",
    )
    parser.add_argument("--ocr", action="store_true", help="Run Phase 2 OCR and save extracted_text.txt")
    parser.add_argument("--clean", action="store_true", help="Run Phase 3 cleaning and save cleaned_text.txt")
    


    args = parser.parse_args()

    if args.verify_env:
        raise SystemExit(verify_env())
    
    if args.url:
        raise SystemExit(run_web_phase(args.url, args.clean, args.max_pages))

    if args.input:
        raise SystemExit(run_phase1(args.input, args.max_pages, args.ocr, args.clean))


    parser.print_help()
    raise SystemExit(2)


if __name__ == "__main__":
    main()
