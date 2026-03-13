from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class CleanResult:
    cleaned_text: str
    removed_lines: List[str]


_PAGE_SPLIT_RE = re.compile(r"(?:\A|\n)\s*----- PAGE (\d+) -----\s*\n", re.IGNORECASE)


def split_pages(raw_text: str) -> List[str]:
    """
    Split the combined OCR text into per-page text blocks.
    Keeps only page bodies (without the PAGE marker).
    """
    if not raw_text:
        return []

    parts = _PAGE_SPLIT_RE.split(raw_text)
    # split returns: [pre, pageNo1, body1, pageNo2, body2, ...]
    if len(parts) < 3:
        return [raw_text]

    pages: List[str] = []
    i = 1
    while i < len(parts) - 1:
        body = parts[i + 1]
        pages.append(body)
        i += 2
    return pages


def join_pages(pages: List[str]) -> str:
    out: List[str] = []
    for idx, body in enumerate(pages, start=1):
        out.append(f"\n\n----- PAGE {idx} -----\n\n")
        out.append(body.strip())
    return "".join(out).strip()


def dehyphenate(text: str) -> str:
    """
    Join words split across line breaks by hyphenation:
      'exam-\\nple' -> 'example'
    Conservative: only when '-' is at end of line and next line starts with a letter.
    """
    return re.sub(r"([A-Za-z])-\s*\n\s*([A-Za-z])", r"\1\2", text)


def normalize_punctuation_spacing(text: str) -> str:
    # Remove space before punctuation: "word ," -> "word,"
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    # Ensure single space after punctuation when followed by a letter/number (basic)
    text = re.sub(r"([,.;:!?])([A-Za-z0-9])", r"\1 \2", text)
    return text


def normalize_whitespace(text: str) -> str:
    # Convert Windows newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Trim trailing spaces per line
    text = "\n".join(line.rstrip() for line in text.splitlines())
    # Collapse 3+ newlines to 2 newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces (keep newlines)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _top_bottom_lines(page: str, n: int = 3) -> Tuple[List[str], List[str]]:
    lines = [ln.strip() for ln in page.splitlines() if ln.strip()]
    if not lines:
        return [], []

    # If the page is too short, header/footer detection becomes unsafe.
    # Require enough lines so top and bottom zones don't swallow the body.
    min_lines_needed = (2 * n) + 2  # e.g., for n=3 -> 8 lines minimum
    if len(lines) < min_lines_needed:
        # Fallback: only consider the very first and very last line
        top = lines[:1]
        bottom = lines[-1:] if len(lines) > 1 else []
        return top, bottom

    top = lines[:n]
    bottom = lines[-n:]
    return top, bottom

def _looks_like_page_number(line: str) -> bool:
    return bool(re.match(r"^\s*page\s*\d+\s*$", line.strip(), re.IGNORECASE))



def remove_repeated_headers_footers(pages: List[str], n_lines: int = 3, min_repeat: int = 2) -> Tuple[List[str], List[str]]:
    """
    Basic heuristic:
    - Look at top N and bottom N non-empty lines of each page.
    - If a line repeats across >= min_repeat pages, treat as header/footer line.
    - Remove those lines from all pages.
    """
    if len(pages) < 2:
        return pages, []

    counts = {}
    for p in pages:
        top, bottom = _top_bottom_lines(p, n=n_lines)
        for ln in (top + bottom):
            counts[ln] = counts.get(ln, 0) + 1

    remove_set = {
    ln for ln, c in counts.items()
    if c >= min_repeat and len(ln) >= 4 and not _looks_like_page_number(ln)
}
    removed = sorted(remove_set)

    cleaned_pages: List[str] = []
    for p in pages:
        lines = p.splitlines()
        new_lines = []
        for ln in lines:
            if ln.strip() in remove_set:
                continue
            new_lines.append(ln)
        cleaned_pages.append("\n".join(new_lines))

    return cleaned_pages, removed


def clean_ocr_text(raw_text: str) -> CleanResult:
    pages = split_pages(raw_text)

    # Header/footer removal works best before heavy whitespace normalization
    pages2, removed = remove_repeated_headers_footers(pages, n_lines=3, min_repeat=2)

    # Clean each page
    cleaned_pages: List[str] = []
    for p in pages2:
        t = p
        t = dehyphenate(t)
        t = normalize_punctuation_spacing(t)
        t = normalize_whitespace(t)
        cleaned_pages.append(t)

    combined = join_pages(cleaned_pages)
    return CleanResult(cleaned_text=combined, removed_lines=removed)
