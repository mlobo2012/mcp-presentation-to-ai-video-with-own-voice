"""PPTX to PDF to PNG conversion using LibreOffice and pdf2image."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from pdf2image import convert_from_path


def convert_pptx_to_pdf(pptx_path: str, libreoffice_path: str) -> Path:
    """Convert a PPTX file to PDF using LibreOffice headless mode."""
    pptx = Path(pptx_path)
    if not pptx.exists():
        raise FileNotFoundError(f"Presentation not found: {pptx_path}")

    tmp_dir = tempfile.mkdtemp(prefix="pptx_convert_")

    cmd = [
        libreoffice_path,
        "--headless",
        "--convert-to", "pdf",
        "--outdir", tmp_dir,
        str(pptx),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(
            f"LibreOffice conversion failed (exit {result.returncode}): {result.stderr}"
        )

    # Find the output PDF - LibreOffice names it after the input file
    pdf_candidates = list(Path(tmp_dir).glob("*.pdf"))
    if not pdf_candidates:
        raise RuntimeError(
            f"LibreOffice produced no PDF output. stdout: {result.stdout}, stderr: {result.stderr}"
        )

    return pdf_candidates[0]


def convert_pdf_to_images(
    pdf_path: Path,
    output_dir: Path,
    poppler_path: str,
    dpi: int = 300,
) -> list[Path]:
    """Convert a PDF to PNG images, one per page."""
    output_dir.mkdir(parents=True, exist_ok=True)

    images = convert_from_path(
        str(pdf_path),
        dpi=dpi,
        poppler_path=poppler_path,
        fmt="png",
    )

    paths = []
    for i, img in enumerate(images, start=1):
        out_path = output_dir / f"slide_{i:03d}.png"
        img.save(str(out_path), "PNG")
        paths.append(out_path)

    return paths


def convert_pptx_to_images(
    pptx_path: str,
    output_dir: Path,
    libreoffice_path: str,
    poppler_path: str,
    dpi: int = 300,
) -> list[Path]:
    """Full pipeline: PPTX → PDF → PNG images."""
    pdf_path = convert_pptx_to_pdf(pptx_path, libreoffice_path)
    try:
        return convert_pdf_to_images(pdf_path, output_dir, poppler_path, dpi)
    finally:
        # Clean up the temporary PDF
        pdf_parent = pdf_path.parent
        if str(pdf_parent).startswith(tempfile.gettempdir()):
            shutil.rmtree(pdf_parent, ignore_errors=True)
