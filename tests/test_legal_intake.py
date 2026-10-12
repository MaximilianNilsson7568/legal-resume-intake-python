import json
from datetime import date

from src.legal_intake import InfraiPdfClient, ResumeDocument, process_resume


class FakeResponse:
    status = 200
    headers = {}

    def read(self):
        return json.dumps({"ok": True, "data": {"skills": ["Python"], "years_experience": 5}}).encode()


def test_due_follow_up_and_pending_delivery_are_explicit():
    client = InfraiPdfClient(api_key="test-key", opener=lambda request: FakeResponse())
    result = process_resume(
        ResumeDocument("A. Lawyer", b"pdf", date(2025, 1, 10)), client, today=date(2025, 1, 11)
    )
    assert result.fields["skills"] == ["Python"]
    assert result.follow_up_due is True
    assert result.delivery_status == "pending"
