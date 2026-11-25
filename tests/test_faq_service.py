import json

import pytest

from app.services.faq_service import load_faqs


def test_faq_records_have_stable_ids_and_optional_category(tmp_path):
    path = tmp_path / "faqs.json"
    path.write_text(json.dumps([{"question":"Where?","answer":"Here","category":"account"}]), encoding="utf-8")
    one = load_faqs(path)
    two = load_faqs(path)
    assert one == two
    assert one[0]["category"] == "account"
    assert one[0]["source_file"] == "faqs.json"


def test_faq_loader_rejects_invalid_record(tmp_path):
    path = tmp_path / "faqs.json"
    path.write_text('[{"question":"missing answer"}]', encoding="utf-8")
    with pytest.raises(ValueError):
        load_faqs(path)
