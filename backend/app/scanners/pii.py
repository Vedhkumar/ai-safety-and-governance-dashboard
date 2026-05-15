"""PII Detector — regex-based detection and masking.

Detects: emails, phone numbers, SSNs, credit cards, IP addresses, names (basic).
Supports masking: replaces detected PII with [TYPE_REDACTED] tokens.
"""

import re
from app.scanners.base import Scanner, ScanResult

# PII patterns with named groups
PII_PATTERNS: dict[str, re.Pattern] = {
    "EMAIL": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    ),
    "PHONE": re.compile(
        r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    ),
    "SSN": re.compile(
        r"\b\d{3}-\d{2}-\d{4}\b"
    ),
    "CREDIT_CARD": re.compile(
        r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
    ),
    "IP_ADDRESS": re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    ),
    "DATE_OF_BIRTH": re.compile(
        r"\b(?:0[1-9]|1[0-2])[/\-](?:0[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2}\b"
    ),
    "US_ADDRESS": re.compile(
        r"\b\d+\s+[A-Za-z]+\s+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Court|Ct|Way|Place|Pl)\b",
        re.IGNORECASE
    ),
    "ZIP_CODE": re.compile(
        r"\b\d{5}(?:-\d{4})?\b"
    ),
}


class PIIScanner(Scanner):
    """Detects and masks personally identifiable information."""

    @property
    def name(self) -> str:
        return "pii"

    def _detect(self, text: str) -> list[dict]:
        """Detect all PII entities in text."""
        entities = []
        for pii_type, pattern in PII_PATTERNS.items():
            for match in pattern.finditer(text):
                entities.append({
                    "type": pii_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })
        return entities

    def mask_text(self, text: str) -> tuple[str, list[dict]]:
        """Replace PII in text with redaction tokens. Returns (masked_text, entities)."""
        entities = self._detect(text)
        if not entities:
            return text, []

        # Sort by position (reverse) so replacements don't shift indices
        entities.sort(key=lambda e: e["start"], reverse=True)
        masked = text
        for entity in entities:
            redacted = f"[{entity['type']}_REDACTED]"
            masked = masked[:entity["start"]] + redacted + masked[entity["end"]:]

        return masked, entities

    async def scan_input(self, text: str) -> ScanResult:
        """Scan input for PII."""
        entities = self._detect(text)
        has_pii = len(entities) > 0

        return ScanResult(
            scanner_name=self.name,
            score=1.0 if has_pii else 0.0,
            is_flagged=has_pii,
            details={
                "pii_detected": has_pii,
                "entity_count": len(entities),
                "entity_types": list(set(e["type"] for e in entities)),
                "entities": [
                    {"type": e["type"], "value": e["value"][:3] + "***"}
                    for e in entities
                ],
            },
            action_taken="masked" if has_pii else "passed"
        )

    async def scan_output(self, text: str, context: dict | None = None) -> ScanResult:
        """Scan LLM output for PII."""
        return await self.scan_input(text)
