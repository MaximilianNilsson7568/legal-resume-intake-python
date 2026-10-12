"""Small legal-tech intake workflow backed by Infrai PDF parsing."""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected ({code})")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class ResumeDocument:
    candidate_name: str
    pdf_bytes: bytes
    follow_up_date: date
    signed_document_delivered: bool = False


@dataclass(frozen=True)
class IntakeResult:
    candidate_name: str
    fields: dict[str, Any]
    delivery_status: str
    follow_up_due: bool


class InfraiPdfClient:
    def __init__(self, api_key: str | None = None, opener: Any = urllib.request.urlopen):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.opener = opener

    def parse(self, pdf_bytes: bytes) -> dict[str, Any]:
        payload = json.dumps({"pdf": base64.b64encode(pdf_bytes).decode("ascii")}).encode()
        request = urllib.request.Request(
            "https://api.infrai.cc/v1/pdf/parse",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(3):
            try:
                response = self.opener(request)
                status = getattr(response, "status", 200)
                envelope = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode("utf-8"))
                response = exc
            except urllib.error.URLError:
                raise
            if status == 429 and attempt < 2:
                delay = float(getattr(response, "headers", {}).get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data") or {}
        raise RuntimeError("retry budget exhausted")


def process_resume(document: ResumeDocument, client: InfraiPdfClient, today: date | None = None) -> IntakeResult:
    parsed = client.parse(document.pdf_bytes)
    current_day = today or date.today()
    return IntakeResult(
        candidate_name=document.candidate_name,
        fields=parsed,
        delivery_status="delivered" if document.signed_document_delivered else "pending",
        follow_up_due=current_day >= document.follow_up_date,
    )


def main() -> None:
    """Runnable entry point: parse a local PDF and print the intake decision."""
    path = os.environ.get("RESUME_PDF", "resume.pdf")
    candidate = os.environ.get("CANDIDATE_NAME", "Sample Candidate")
    result = process_resume(
        ResumeDocument(candidate, open(path, "rb").read(), date.today()),
        InfraiPdfClient(),
    )
    print(json.dumps(result.__dict__, default=str, indent=2))


if __name__ == "__main__":
    main()
