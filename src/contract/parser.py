"""
Contract Parser — T4.1 (Người C)

Parses contract documents (PDF, DOCX, TXT) to Markdown using MinerU CLI,
with PII detection and redaction for Vietnamese contracts.

Usage:
    from contract import ContractParser

    parser = ContractParser()
    contract = parser.parse("path/to/contract.pdf")
    print(contract.redacted_text)
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import uuid
from datetime import date
from pathlib import Path
from typing import Optional

from .models import Contract, ParseError
from .pii import detect_pii, redact_pii


SUPPORTED_FORMATS = {".pdf", ".docx", ".txt"}


class ContractParser:
    """
    Parse contract documents to Markdown with PII redaction.

    Uses MinerU CLI for document parsing (PDF/DOCX/TXT → Markdown).
    Automatically detects and redacts Vietnamese PII.
    """

    def __init__(
        self,
        output_dir: Optional[str] = None,
        lang: str = "ch",  # MinerU uses "ch" for Chinese/Vietnamese OCR
        backend: str = "pipeline",
    ) -> None:
        """
        Initialize ContractParser.

        Args:
            output_dir: Temporary output directory for MinerU (auto-created if None)
            lang: OCR language code for MinerU
            backend: MinerU backend ("pipeline" for CPU, "vlm-auto-engine" for GPU)
        """
        self._output_dir = output_dir
        self._lang = lang
        self._backend = backend

    def parse(
        self,
        file_path: str,
        do_redact_pii: bool = True,
    ) -> Contract:
        """
        Parse a contract document.

        Args:
            file_path: Path to PDF, DOCX, or TXT file
            do_redact_pii: Whether to detect and redact PII (default: True)

        Returns:
            Contract object with raw_text, redacted_text, and pii_map

        Raises:
            ParseError: If parsing fails
        """
        path = Path(file_path)

        # Validate file exists
        if not path.exists():
            raise ParseError(
                f"File not found: {file_path}",
                file_path=file_path,
                error_type="unknown",
            )

        # Validate format
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_FORMATS:
            raise ParseError(
                f"Unsupported format: {suffix}. Supported: {SUPPORTED_FORMATS}",
                file_path=file_path,
                error_type="unsupported",
            )

        # Parse based on format
        if suffix == ".txt":
            raw_text = self._read_txt(path)
        else:
            # Parse with MinerU for PDF/DOCX
            try:
                raw_text = self._run_mineru(path)
            except ParseError:
                raise
            except Exception as e:
                raise ParseError(
                    f"MinerU parsing failed: {str(e)}",
                    file_path=file_path,
                    error_type="unknown",
                    original_exception=e,
                )

        # PII detection and redaction
        pii_matches = detect_pii(raw_text) if do_redact_pii else []
        redacted_text, pii_map = redact_pii(raw_text, pii_matches) if do_redact_pii else (raw_text, {})

        return Contract(
            id=str(uuid.uuid4()),
            raw_text=raw_text,
            redacted_text=redacted_text,
            source_format=suffix.lstrip("."),
            upload_date=date.today(),
            pii_map=pii_map,
            metadata={
                "file_size": path.stat().st_size,
                "file_name": path.name,
            },
        )

    def _read_txt(self, path: Path) -> str:
        """
        Read TXT file directly without MinerU.

        Args:
            path: Path to TXT file

        Returns:
            Text content

        Raises:
            ParseError: If reading fails
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try latin-1 as fallback
            with open(path, "r", encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            raise ParseError(
                f"Failed to read TXT file: {str(e)}",
                file_path=str(path),
                error_type="corrupted",
                original_exception=e,
            )

    def _run_mineru(self, path: Path) -> str:
        """
        Run MinerU CLI to parse document to Markdown.

        Args:
            path: Path to document

        Returns:
            Markdown text output

        Raises:
            ParseError: If MinerU fails
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                "mineru",
                "--path", str(path),
                "--output", tmpdir,
                "--lang", self._lang,
                "--backend", self._backend,
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )
            except subprocess.TimeoutExpired:
                raise ParseError(
                    "MinerU parsing timed out (5 minutes)",
                    file_path=str(path),
                    error_type="ocr_failure",
                )
            except Exception as e:
                raise ParseError(
                    f"Failed to run MinerU: {str(e)}",
                    file_path=str(path),
                    error_type="unknown",
                    original_exception=e,
                )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or "MinerU exited with non-zero code"
                raise ParseError(
                    f"MinerU error: {error_msg}",
                    file_path=str(path),
                    error_type="ocr_failure",
                )

            # Read output Markdown
            md_content = self._read_mineru_output(tmpdir, path)
            return md_content

    def _read_mineru_output(self, tmpdir: str, path: Path) -> str:
        """
        Read MinerU output Markdown from temp directory.

        MinerU outputs to: {tmpdir}/{filename_without_ext}/{filename}.md

        Args:
            tmpdir: Temporary directory used by MinerU
            path: Original file path

        Returns:
            Markdown content

        Raises:
            ParseError: If output not found
        """
        # MinerU creates a subdirectory with the filename (without extension)
        stem = path.stem
        output_dir = os.path.join(tmpdir, stem)

        if not os.path.exists(output_dir):
            # Try listing what's in tmpdir
            contents = os.listdir(tmpdir)
            if contents:
                output_dir = os.path.join(tmpdir, contents[0])
            else:
                raise ParseError(
                    "MinerU produced no output",
                    file_path=str(path),
                    error_type="ocr_failure",
                )

        # Find .md file
        md_files = [f for f in os.listdir(output_dir) if f.endswith(".md")]
        if not md_files:
            # Try .txt file as fallback
            txt_files = [f for f in os.listdir(output_dir) if f.endswith(".txt")]
            if txt_files:
                with open(os.path.join(output_dir, txt_files[0]), "r", encoding="utf-8") as f:
                    return f.read()
            raise ParseError(
                "No Markdown output found from MinerU",
                file_path=str(path),
                error_type="ocr_failure",
            )

        # Read the first .md file
        md_path = os.path.join(output_dir, md_files[0])
        with open(md_path, "r", encoding="utf-8") as f:
            return f.read()
