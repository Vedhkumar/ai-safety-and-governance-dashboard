"""Bias Detector — pattern matching for stereotypical and biased language."""

import re
from app.scanners.base import Scanner, ScanResult

BIAS_PATTERNS = [
    (r"\b(all|every)\s+(women|men|blacks|whites|asians|latinos|muslims|jews|christians)\s+(are|is)\b", "demographic_generalization"),
    (r"\b(women|girls)\s+(should|must|need\s+to)\s+(stay|be|remain)\b", "gender_prescription"),
    (r"\b(men|boys)\s+(don'?t|shouldn'?t|can'?t)\s+(cry|show\s+emotion|be\s+sensitive)\b", "toxic_masculinity"),
    (r"\b(typical|classic)\s+(woman|man|asian|black|white|latino)\b", "stereotyping"),
    (r"\byou\s+people\b", "othering"),
    (r"\b(naturally|inherently|biologically)\s+(better|worse|superior|inferior)\b", "biological_determinism"),
    (r"\b(civilized|uncivilized|primitive|savage)\s+(people|culture|nation)\b", "cultural_supremacy"),
    (r"\b(poor|rich)\s+because\s+(they|their)\b", "socioeconomic_bias"),
    (r"\b(too\s+old|too\s+young)\s+to\b", "age_discrimination"),
    (r"\b(disabled|handicapped)\s+people\s+(can'?t|shouldn'?t|unable)\b", "ableism"),
]

COMPILED_BIAS_PATTERNS = [(re.compile(p, re.IGNORECASE), name) for p, name in BIAS_PATTERNS]


class BiasScanner(Scanner):
    @property
    def name(self) -> str:
        return "bias"

    def _scan_text(self, text: str) -> ScanResult:
        matches = []
        for pattern, name in COMPILED_BIAS_PATTERNS:
            found = pattern.findall(text)
            if found:
                matches.append({"pattern": name, "count": len(found)})
        total = len(matches)
        score = min(0.3 + total * 0.2, 1.0) if total > 0 else 0.0
        return ScanResult(
            scanner_name=self.name, score=round(score, 3), is_flagged=score > 0.5,
            details={"bias_patterns_found": matches, "total_matches": total})

    async def scan_input(self, text: str) -> ScanResult:
        return self._scan_text(text)

    async def scan_output(self, text: str, context: dict | None = None) -> ScanResult:
        return self._scan_text(text)
