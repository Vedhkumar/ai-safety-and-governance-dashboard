"""Hallucination Detector — claim-level verification using TF-IDF similarity."""

import re
import numpy as np
from app.scanners.base import Scanner, ScanResult


def split_into_claims(text: str) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 15] or [text.strip()]


class HallucinationScanner(Scanner):
    def __init__(self):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2), stop_words="english")
        except ImportError:
            self._vectorizer = None

    @property
    def name(self) -> str:
        return "hallucination"

    def _compute_similarity(self, claims: list[str], sources: list[str]) -> list[dict]:
        if not self._vectorizer or not sources or not claims:
            return [{"claim": c, "similarity_score": 0.5, "is_supported": True, "supporting_source": None} for c in claims]
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            all_texts = sources + claims
            tfidf_matrix = self._vectorizer.fit_transform(all_texts)
            source_vectors = tfidf_matrix[:len(sources)]
            claim_vectors = tfidf_matrix[len(sources):]
            results = []
            for i, claim in enumerate(claims):
                sims = cosine_similarity(claim_vectors[i:i+1], source_vectors).flatten()
                max_sim = float(np.max(sims)) if len(sims) > 0 else 0.0
                best_idx = int(np.argmax(sims)) if len(sims) > 0 else 0
                results.append({"claim": claim, "similarity_score": round(max_sim, 3),
                    "is_supported": max_sim > 0.3,
                    "supporting_source": sources[best_idx][:100] if max_sim > 0.3 else None})
            return results
        except Exception:
            return [{"claim": c, "similarity_score": 0.5, "is_supported": True, "supporting_source": None} for c in claims]

    async def scan_input(self, text: str) -> ScanResult:
        return ScanResult(scanner_name=self.name, score=0.0, is_flagged=False,
            details={"note": "hallucination scanning is output-only"})

    async def scan_output(self, text: str, context: dict | None = None) -> ScanResult:
        source_docs = (context or {}).get("source_documents", [])
        claims = split_into_claims(text)
        claim_results = self._compute_similarity(claims, source_docs)
        unsupported = [r for r in claim_results if not r["is_supported"]]
        if not claim_results:
            overall_score = 0.0
        elif not source_docs:
            overall_score = 0.3
        else:
            overall_score = len(unsupported) / len(claim_results)
        return ScanResult(scanner_name=self.name, score=round(overall_score, 3),
            is_flagged=overall_score > 0.5,
            details={"overall_score": round(overall_score, 3), "total_claims": len(claim_results),
                "unsupported_claims": len(unsupported), "has_source_docs": bool(source_docs),
                "claims": claim_results[:10], "method": "semantic_similarity" if source_docs else "baseline"})
