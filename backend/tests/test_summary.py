"""Tests for the summary service — JSON parsing, cache hit/miss, page labels."""
import json
from unittest.mock import MagicMock

import pytest
import structlog

from app.core.errors import AppError
from app.services.summary import (
    StructuredSummary,
    _page_label,
    _parse_summary_json,
)


@pytest.fixture
def log():
    return structlog.get_logger()


class TestParseSummaryJson:
    def test_valid_json(self, log):
        content = json.dumps({
            "executive_summary": ["Point 1", "Point 2"],
            "key_concepts": ["Concept A"],
            "definitions": {"term1": "def1"},
            "possible_questions": ["Q1"],
        })

        result = _parse_summary_json(content, log)

        assert isinstance(result, StructuredSummary)
        assert result.executive_summary == ["Point 1", "Point 2"]
        assert result.key_concepts == ["Concept A"]
        assert result.definitions == {"term1": "def1"}
        assert result.possible_questions == ["Q1"]

    def test_strips_code_fences(self, log):
        content = '```json\n{"executive_summary": ["P1"], "key_concepts": ["C1"], "definitions": {}, "possible_questions": ["Q1"]}\n```'

        result = _parse_summary_json(content, log)

        assert result.executive_summary == ["P1"]

    def test_invalid_json_raises_503(self, log):
        with pytest.raises(AppError) as exc_info:
            _parse_summary_json("not valid json {{{", log)
        assert exc_info.value.status_code == 503

    def test_missing_field_raises_503(self, log):
        content = json.dumps({
            "executive_summary": ["P1"],
            # missing key_concepts, definitions, possible_questions
        })

        with pytest.raises(AppError) as exc_info:
            _parse_summary_json(content, log)
        assert exc_info.value.status_code == 503

    def test_wrong_types_raises_503(self, log):
        content = json.dumps({
            "executive_summary": "not a list",
            "key_concepts": ["C1"],
            "definitions": {},
            "possible_questions": ["Q1"],
        })

        with pytest.raises(AppError) as exc_info:
            _parse_summary_json(content, log)
        assert exc_info.value.status_code == 503


class TestStructuredSummary:
    def test_frozen(self):
        s = StructuredSummary(
            executive_summary=["P1"],
            key_concepts=["C1"],
            definitions={"t": "d"},
            possible_questions=["Q1"],
        )
        with pytest.raises(AttributeError):
            s.executive_summary = ["changed"]


class TestPageLabel:
    def test_none(self):
        assert _page_label(None, None) == "Pages unknown"

    def test_single(self):
        assert _page_label(3, 3) == "Page 3"

    def test_range(self):
        assert _page_label(1, 5) == "Pages 1-5"
