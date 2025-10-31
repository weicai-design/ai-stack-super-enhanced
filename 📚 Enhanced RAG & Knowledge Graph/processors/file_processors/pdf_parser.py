"""
Lightweight PDF parser for the emoji-named processors package.
Optional dependency: PyPDF2.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List

try:
    from pypdf import PdfReader as _PdfReader  # 优先使用 pypdf

    _PDF_BACKEND = "pypdf"
except Exception:
    try:
        import PyPDF2

        _PdfReader = PyPDF2.PdfReader  # 兼容回退
        _PDF_BACKEND = "PyPDF2"
    except Exception as e:
        _PdfReader = None
        _IMPORT_ERR = e
        _PDF_BACKEND = "none"


def _md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_pdf(path: str | Path) -> List[Dict]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    if _PdfReader is None:
        raise ImportError(
            f"No PDF backend available: {_IMPORT_ERR if ' _IMPORT_ERR' in globals() else 'pypdf/PyPDF2 not installed'}"
        )

    reader = _PdfReader(str(p))
    checksum = _md5_file(p)
    results: List[Dict] = []
    # pypdf 与 PyPDF2 都有 pages
    for i, page in enumerate(getattr(reader, "pages", []), start=1):
        try:
            # pypdf: extract_text; PyPDF2: extract_text 也可用
            text = page.extract_text() or ""
        except Exception:
            text = ""
        results.append(
            {
                "text": text,
                "source": str(p),
                "page": i,
                "checksum": checksum,
            }
        )
    return results
