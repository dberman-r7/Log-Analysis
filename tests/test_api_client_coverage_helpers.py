"""Small coverage tests for API client helper branches.

These validate defensive code paths (fail-soft observability helpers) without
changing runtime behavior.
"""

from unittest.mock import Mock


def test_headers_as_dict_handles_non_dict_headers():
    from src.log_ingestion.api_client import Rapid7ApiClient

    resp = Mock()

    class _Headers:
        def keys(self):
            return ["X-Test"]

        def __getitem__(self, key):
            return "1"

    resp.headers = _Headers()

    out = Rapid7ApiClient._headers_as_dict(resp)
    assert out == {"X-Test": "1"}


def test_body_preview_handles_non_string_text():
    from src.log_ingestion.api_client import Rapid7ApiClient

    resp = Mock()
    resp.text = 12345  # non-string

    preview = Rapid7ApiClient._body_preview(resp)
    assert isinstance(preview, str)
    assert "12345" in preview
