"""
Lightweight PDF parser with optional dependency on PyPDF2.

Functions:
    - parse_pdf(file_path) -> list[dict]

Behavior:
    - If PyPDF2 is not installed, parse_pdf raises ImportError.
    - If file not found, FileNotFoundError is raised.
"""

from __future__ import annotations

import hashlib
import os
from typing import Dict, List


def _file_checksum(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def parse_pdf(file_path: str) -> List[Dict]:
    """Parse a PDF into a list of chunk dicts.

    Each chunk has at least: text, source, page, start_offset,
    end_offset and checksum.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    try:
        import PyPDF2
    except Exception as e:
        raise ImportError("PyPDF2 is required to parse PDFs") from e

    reader = PyPDF2.PdfReader(file_path)
    checksum = _file_checksum(file_path)
    chunks = []
    for page_idx, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            # extraction errors should not break the whole flow
            text = ""

        chunk = {
            "text": text,
            "source": os.path.abspath(file_path),
            "page": page_idx + 1,
            "start_offset": 0,
            "end_offset": len(text),
            "checksum": checksum,
        }
        chunks.append(chunk)

    return chunks
