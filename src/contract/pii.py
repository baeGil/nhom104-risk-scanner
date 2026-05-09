"""
PII Detection and Redaction for Vietnamese contracts.

Detects and redacts:
- CCCD/CMND (9-12 digit ID numbers)
- Mã số thuế (10-13 digit tax codes)
- Phone numbers (+84/0 prefix, 9-11 digits)
- Email addresses
- Bank account numbers (10-16 digits with banking context)
- Vietnamese addresses (with location keywords)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class PIIMatch:
    """A single PII match found in text."""
    pii_type: str           # "cccd", "mst", "phone", "email", "address", "bank_account"
    value: str              # The original PII value
    start: int              # Start position in text
    end: int                # End position in text
    confidence: float = 1.0 # Confidence score (0-1)


# ---------------------------------------------------------------------------
# Regex patterns for Vietnamese PII
# ---------------------------------------------------------------------------

# CCCD/CMND: 9-12 digits, often appears after "CCCD", "CMND", "Số:"
RE_CCCD = re.compile(
    r"(?:CCCD|CMND|Căn\s*cước\s*(?:công\s*dân)?|Chứng\s*nhân\s*dân|Số)\s*(?:số\s*)?[:\-]?\s*(\d{9,12})\b",
    re.IGNORECASE,
)

# Mã số thuế: 10-13 digits, often after "MST", "Mã số thuế", "Thuế"
RE_MST = re.compile(
    r"(?:MST|Mã\s*số\s*thuế|Thuế\s*):\s*[:\-]?\s*(\d{10,13})\b",
    re.IGNORECASE,
)

# Phone: +84 or 0 prefix, 9-11 digits total
RE_PHONE = re.compile(
    r"(?:\+84|0)(\d{8,10})\b"
    r"|"
    r"(\+84[\s\-]?\d{1,3}[\s\-]?\d{3,4}[\s\-]?\d{3,4})\b",
)

# Email: standard email pattern
RE_EMAIL = re.compile(
    r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b",
)

# Bank account: 10-16 digits with banking context
RE_BANK_ACCOUNT = re.compile(
    r"(?:STK|Số\s*tài\s*khoản|Tài\s*khoản|Ngân\s*hàng|Bank|Account)\s*[:\-]?\s*(\d{10,16})\b",
    re.IGNORECASE,
)

# Vietnamese address: keywords + content (more specific to avoid false positives)
RE_ADDRESS = re.compile(
    r"(?:đường|phố|ngõ|hẻm|quận|huyện|phường|xã|tỉnh|thành\s*phố|TP\.)"
    r"\s+[^,.\n]{3,50}",
    re.IGNORECASE,
)

# Standalone digit sequences that might be CCCD/MST (need context filtering)
RE_STANDALONE_DIGITS = re.compile(
    r"\b(\d{9,13})\b",
)


def detect_pii(text: str) -> list[PIIMatch]:
    """
    Detect PII in text and return list of PIIMatch objects.

    Args:
        text: Input text to scan for PII

    Returns:
        List of PIIMatch objects with type, value, and position
    """
    matches: list[PIIMatch] = []

    # CCCD
    for m in RE_CCCD.finditer(text):
        value = m.group(1) if m.group(1) else m.group(0)
        start = m.start(1) if m.group(1) else m.start()
        end = m.end(1) if m.group(1) else m.end()
        matches.append(PIIMatch(
            pii_type="cccd",
            value=value,
            start=start,
            end=end,
        ))

    # MST
    for m in RE_MST.finditer(text):
        value = m.group(1) if m.group(1) else m.group(0)
        start = m.start(1) if m.group(1) else m.start()
        end = m.end(1) if m.group(1) else m.end()
        matches.append(PIIMatch(
            pii_type="mst",
            value=value,
            start=start,
            end=end,
        ))

    # Phone
    for m in RE_PHONE.finditer(text):
        value = m.group(0)
        matches.append(PIIMatch(
            pii_type="phone",
            value=value,
            start=m.start(),
            end=m.end(),
        ))

    # Email
    for m in RE_EMAIL.finditer(text):
        value = m.group(1) if m.group(1) else m.group(0)
        matches.append(PIIMatch(
            pii_type="email",
            value=value,
            start=m.start(),
            end=m.end(),
        ))

    # Bank account
    for m in RE_BANK_ACCOUNT.finditer(text):
        value = m.group(1) if m.group(1) else m.group(0)
        start = m.start(1) if m.group(1) else m.start()
        end = m.end(1) if m.group(1) else m.end()
        matches.append(PIIMatch(
            pii_type="bank_account",
            value=value,
            start=start,
            end=end,
        ))

    # Address
    for m in RE_ADDRESS.finditer(text):
        value = m.group(0).strip()
        if len(value) > 5:  # Filter very short matches
            matches.append(PIIMatch(
                pii_type="address",
                value=value,
                start=m.start(),
                end=m.end(),
                confidence=0.8,  # Lower confidence for addresses
            ))

    # Deduplicate overlapping matches (keep longest/highest confidence)
    matches = _deduplicate_matches(matches)

    return matches


def redact_pii(
    text: str,
    pii_matches: Optional[list[PIIMatch]] = None,
) -> tuple[str, dict[str, str]]:
    """
    Redact PII from text and return redacted text + mapping.

    Args:
        text: Input text
        pii_matches: Optional pre-detected PII matches (if None, auto-detect)

    Returns:
        Tuple of (redacted_text, pii_map)
        pii_map: {"[REDACTED_CCCD_1]": "079087654321", ...}
    """
    if pii_matches is None:
        pii_matches = detect_pii(text)

    if not pii_matches:
        return text, {}

    # Sort by start position (reverse order for safe replacement)
    pii_matches.sort(key=lambda m: m.start, reverse=True)

    pii_map: dict[str, str] = {}
    counters: dict[str, int] = {}
    redacted = text

    for match in pii_matches:
        # Generate placeholder
        pii_type = match.pii_type.upper()
        counters[pii_type] = counters.get(pii_type, 0) + 1
        placeholder = f"[REDACTED_{pii_type}_{counters[pii_type]}]"
        pii_map[placeholder] = match.value

        # Replace in text
        redacted = redacted[:match.start] + placeholder + redacted[match.end:]

    return redacted, pii_map


def reconstruct_text(redacted_text: str, pii_map: dict[str, str]) -> str:
    """
    Reconstruct original text from redacted text and PII map.

    Args:
        redacted_text: Text with PII placeholders
        pii_map: Mapping of placeholder → original value

    Returns:
        Original text with PII restored
    """
    text = redacted_text
    for placeholder, original_value in pii_map.items():
        text = text.replace(placeholder, original_value)
    return text


def _deduplicate_matches(matches: list[PIIMatch]) -> list[PIIMatch]:
    """
    Remove overlapping PII matches, keeping the longest/highest confidence.
    """
    if not matches:
        return []

    # Sort by start position, then by length (descending)
    sorted_matches = sorted(matches, key=lambda m: (m.start, -(m.end - m.start)))

    result: list[PIIMatch] = []
    last_end = -1

    for match in sorted_matches:
        if match.start >= last_end:
            result.append(match)
            last_end = match.end
        else:
            # Overlapping - keep the one with higher confidence or longer value
            if result and (match.end - match.start) > (result[-1].end - result[-1].start):
                result[-1] = match
                last_end = match.end

    return result
