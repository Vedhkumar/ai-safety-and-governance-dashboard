"""Safety Scanner Pipeline — orchestrates all scanners in parallel."""

import asyncio
from app.scanners.base import ScanResult
from app.scanners.injection import InjectionScanner
from app.scanners.toxicity import ToxicityScanner
from app.scanners.pii import PIIScanner
from app.scanners.hallucination import HallucinationScanner
from app.scanners.bias import BiasScanner


class ScanPipeline:
    """Orchestrates all safety scanners, running them in parallel."""

    def __init__(self):
        self.injection = InjectionScanner()
        self.toxicity = ToxicityScanner()
        self.pii = PIIScanner()
        self.hallucination = HallucinationScanner()
        self.bias = BiasScanner()

    async def scan_input(self, text: str) -> dict[str, ScanResult]:
        """Run all input scanners in parallel."""
        results = await asyncio.gather(
            self.injection.scan_input(text),
            self.toxicity.scan_input(text),
            self.pii.scan_input(text),
            self.bias.scan_input(text),
            return_exceptions=True,
        )
        scanner_names = ["injection", "toxicity", "pii", "bias"]
        output = {}
        for name, result in zip(scanner_names, results):
            if isinstance(result, Exception):
                output[name] = ScanResult(scanner_name=name, score=0.0, details={"error": str(result)})
            else:
                output[name] = result
        return output

    async def scan_output(self, text: str, context: dict | None = None) -> dict[str, ScanResult]:
        """Run all output scanners in parallel."""
        results = await asyncio.gather(
            self.hallucination.scan_output(text, context),
            self.toxicity.scan_output(text),
            self.bias.scan_output(text),
            self.pii.scan_output(text),
            return_exceptions=True,
        )
        scanner_names = ["hallucination", "toxicity", "bias", "pii"]
        output = {}
        for name, result in zip(scanner_names, results):
            if isinstance(result, Exception):
                output[name] = ScanResult(scanner_name=name, score=0.0, details={"error": str(result)})
            else:
                output[name] = result
        return output

    def mask_pii(self, text: str) -> tuple[str, list[dict]]:
        """Mask PII in text. Returns (masked_text, entities)."""
        return self.pii.mask_text(text)


# Global singleton
pipeline = ScanPipeline()
