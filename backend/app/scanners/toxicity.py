"""Toxicity Classifier — keyword/pattern-based with category scoring.

Lightweight replacement for unitary/toxic-bert. Scores across 6 categories:
toxic, severe_toxic, obscene, threat, insult, identity_hate.
"""

import re
from app.scanners.base import Scanner, ScanResult

# Category-specific keyword patterns (simplified for lightweight mode)
TOXICITY_PATTERNS: dict[str, list[str]] = {
    "toxic": [
        r"\bstupid\b", r"\bidiot\b", r"\bmoron\b", r"\bshut\s+up\b",
        r"\bdumb\b", r"\bloser\b", r"\bpathetic\b", r"\bworthless\b",
        r"\buseless\b", r"\bdisgust(ing)?\b", r"\bgarbage\b", r"\btrash\b",
    ],
    "severe_toxic": [
        r"\bdie\b.*\b(please|now|already)\b", r"\bkill\s+your", r"\bwish.*dead\b",
        r"\bhope.*die\b", r"\brot\s+in\b",
    ],
    "obscene": [
        r"\bf+u+c+k+\b", r"\bs+h+i+t+\b", r"\ba+s+s+h+o+l+e+\b",
        r"\bb+i+t+c+h+\b", r"\bd+a+m+n+\b", r"\bh+e+l+l+\b",
        r"\bcrap\b", r"\bwtf\b", r"\bstfu\b",
    ],
    "threat": [
        r"\b(i('ll|m\s+going\s+to|will)\s+)?(kill|hurt|harm|attack|destroy)\s+(you|them|him|her)\b",
        r"\byou('re|\s+are)\s+dead\b", r"\bwatch\s+your\s+back\b",
        r"\bi('ll|m\s+going\s+to)\s+find\s+you\b", r"\bthreat(en)?\b",
        r"\bbomb\b", r"\bgun\b.*\bshoot\b",
    ],
    "insult": [
        r"\bugly\b", r"\bfat\b", r"\bstupid\b", r"\bidiot\b",
        r"\bclown\b", r"\bjoke\b.*\byou\b", r"\bpathetic\b",
        r"\bembarrass(ing|ment)?\b", r"\bweak\b", r"\bcoward\b",
    ],
    "identity_hate": [
        r"\b(racial|ethnic)\s+slur\b", r"\bhate\s+(all\s+)?(women|men|people)\b",
        r"\b(sexist|racist|homophob|transphob|bigot)\b",
        r"\bdon'?t\s+belong\b", r"\bgo\s+back\s+to\b",
        r"\bsubhuman\b", r"\binferior\s+(race|gender|people)\b",
    ],
}


class ToxicityScanner(Scanner):
    """Detects toxic content across multiple categories."""

    def __init__(self):
        self._compiled_patterns: dict[str, list[re.Pattern]] = {}
        for category, patterns in TOXICITY_PATTERNS.items():
            self._compiled_patterns[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    @property
    def name(self) -> str:
        return "toxicity"

    def _score_text(self, text: str) -> dict[str, float]:
        """Score text across all toxicity categories."""
        scores = {}
        for category, patterns in self._compiled_patterns.items():
            match_count = sum(1 for p in patterns if p.search(text))
            total_patterns = len(patterns)
            # Score based on proportion of patterns matched, with diminishing returns
            if match_count == 0:
                scores[category] = 0.0
            else:
                scores[category] = min(0.3 + (match_count / total_patterns) * 0.7, 1.0)
        return scores

    async def scan_input(self, text: str) -> ScanResult:
        """Scan input text for toxicity."""
        scores = self._score_text(text)
        max_score = max(scores.values()) if scores else 0.0

        return ScanResult(
            scanner_name=self.name,
            score=round(max_score, 3),
            is_flagged=max_score > 0.5,
            details={
                "category_scores": {k: round(v, 3) for k, v in scores.items()},
                "max_category": max(scores, key=scores.get) if max_score > 0 else "none",
            },
            action_taken="passed"
        )

    async def scan_output(self, text: str, context: dict | None = None) -> ScanResult:
        """Scan LLM output for toxicity."""
        return await self.scan_input(text)
