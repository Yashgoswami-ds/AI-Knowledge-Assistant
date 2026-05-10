from src.link_extractor import extract_from_url
from src.pdf_handler import handle_pdf_upload


class DummyUpload:
    filename = "dummy.pdf"

    def save(self, _path):
        return None


def test_extract_invalid_url_returns_error():
    ok, message = extract_from_url("not-a-url")
    assert ok is False
    assert "Invalid URL" in message

def test_pdf_upload_saves_to_knowledge(monkeypatch):
    monkeypatch.setattr("src.pdf_handler.PDF_AVAILABLE", True)
    # Avoid actual PDF parsing in test: stub extraction to return sample chunks
    monkeypatch.setattr("src.pdf_handler.extract_pdf_text", lambda path: (["sample text chunk"], None))
    success, message = handle_pdf_upload(DummyUpload())
    assert success is True
    assert "processed" in message or "saved" in message
