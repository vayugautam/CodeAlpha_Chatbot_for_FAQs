from types import SimpleNamespace

import pytest

from app.services.llm_service import generate_answer


class FakeGroq:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=next(self.responses)))])


def test_answer_citation_and_evidence_verification():
    record = {"faq_id":"faq-1","question":"How?","answer":"Use the dashboard.","similarity":0.9}
    client = FakeGroq(['{"answer":"Use the dashboard.","citations":[{"faq_id":"faq-1"}],"insufficient_evidence":false}', '{"supported":true,"reason":"The FAQ states this."}'])
    result = generate_answer("How?", [record], client)
    assert result["sources"][0]["faq_id"] == "faq-1"


def test_answer_rejects_fabricated_faq_citation():
    record = {"faq_id":"faq-1","question":"How?","answer":"Use the dashboard.","similarity":0.9}
    client = FakeGroq(['{"answer":"Unsupported.","citations":[{"faq_id":"fake"}],"insufficient_evidence":false}'])
    with pytest.raises(ValueError, match="not retrieved"):
        generate_answer("How?", [record], client)
