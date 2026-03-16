"""Tests for the analysis module."""

import pytest

from analysis import (
    aggregate_scores,
    analyze_refusals,
    compute_inter_rater_reliability,
    extract_low_scores,
    extract_quotes,
    summary_table,
)


def _ann(model="DALL-E 3", model_key="dalle", category="profession",
         background="Pakistan", prompt="A doctor", prompt_type="free",
         status="success", scores=None, **kwargs):
    """Helper to build a minimal annotation dict for testing."""
    return {
        "participant_id": kwargs.get("pid", "P-test"),
        "background": background,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "prompt_type": prompt_type,
        "prompt": prompt,
        "category": category,
        "model": model_key,
        "model_name": model,
        "status": status,
        "scores": scores,
        "refusal_note": kwargs.get("refusal_note"),
        "expectation": kwargs.get("expectation"),
        "authenticity_note": kwargs.get("authenticity_note"),
        "harm_note": kwargs.get("harm_note"),
    }


SAMPLE = [
    _ann(scores={"authenticity": 2, "diversity": 1, "respectfulness": 3}),
    _ann(scores={"authenticity": 4, "diversity": 4, "respectfulness": 5}),
    _ann(model="Stable Diffusion XL", model_key="stable_diffusion",
         scores={"authenticity": 1, "diversity": 1, "respectfulness": 1}),
    _ann(model="Stable Diffusion XL", model_key="stable_diffusion",
         background="Iran",
         scores={"authenticity": 3, "diversity": 2, "respectfulness": 2}),
]


class TestAggregateScores:
    def test_by_model(self):
        result = aggregate_scores(SAMPLE, "model_name")
        assert "DALL-E 3" in result
        assert "Stable Diffusion XL" in result
        assert result["DALL-E 3"]["n"] == 2
        assert result["Stable Diffusion XL"]["n"] == 2

    def test_by_background(self):
        result = aggregate_scores(SAMPLE, "background")
        assert "Pakistan" in result
        assert "Iran" in result
        assert result["Pakistan"]["n"] == 3
        assert result["Iran"]["n"] == 1

    def test_by_category(self):
        result = aggregate_scores(SAMPLE, "category")
        assert "profession" in result
        assert result["profession"]["n"] == 4

    def test_skips_missing_scores(self):
        anns = [_ann(status="refused", scores=None)]
        result = aggregate_scores(anns, "model_name")
        assert result == {}

    def test_mean_values(self):
        result = aggregate_scores(SAMPLE, "model_name")
        dalle = result["DALL-E 3"]
        assert dalle["authenticity_mean"] == pytest.approx(3.0)  # (2+4)/2
        assert dalle["diversity_mean"] == pytest.approx(2.5)     # (1+4)/2


class TestAnalyzeRefusals:
    def test_counts(self):
        anns = [
            _ann(status="refused", scores=None, refusal_note="Erases us"),
            _ann(status="refused", scores=None, model="Stable Diffusion XL",
                 refusal_note="Also erases us"),
            _ann(scores={"authenticity": 3, "diversity": 3, "respectfulness": 3}),
        ]
        result = analyze_refusals(anns)
        assert result["total"] == 2
        assert len(result["by_model"]["DALL-E 3"]) == 1
        assert len(result["by_model"]["Stable Diffusion XL"]) == 1

    def test_no_refusals(self):
        result = analyze_refusals(SAMPLE)
        assert result["total"] == 0


class TestInterRaterReliability:
    def test_shared_prompts(self):
        anns = [
            _ann(prompt_type="shared", pid="P-a",
                 scores={"authenticity": 2, "diversity": 3, "respectfulness": 4}),
            _ann(prompt_type="shared", pid="P-b",
                 scores={"authenticity": 4, "diversity": 3, "respectfulness": 2}),
        ]
        result = compute_inter_rater_reliability(anns)
        key = "A doctor | DALL-E 3"
        assert key in result
        assert result[key]["n_raters"] == 2
        assert result[key]["authenticity_mean"] == pytest.approx(3.0)
        assert result[key]["authenticity_range"] == 2

    def test_ignores_free_prompts(self):
        anns = [_ann(prompt_type="free", scores={"authenticity": 1, "diversity": 1, "respectfulness": 1})]
        result = compute_inter_rater_reliability(anns)
        assert result == {}


class TestExtractLowScores:
    def test_finds_low_scores(self):
        findings = extract_low_scores(SAMPLE, threshold=2)
        # SD has authenticity=1, diversity=1, respectfulness=1
        assert len(findings["authenticity"]["Stable Diffusion XL"]) >= 1
        assert len(findings["diversity"]["DALL-E 3"]) >= 1  # first DALL-E has diversity=1

    def test_empty_with_high_scores(self):
        anns = [_ann(scores={"authenticity": 5, "diversity": 5, "respectfulness": 5})]
        findings = extract_low_scores(anns)
        for field_findings in findings.values():
            assert len(field_findings) == 0


class TestExtractQuotes:
    def test_length_filter(self):
        anns = [
            _ann(scores={"authenticity": 1, "diversity": 1, "respectfulness": 1},
                 harm_note="Short"),
            _ann(scores={"authenticity": 1, "diversity": 1, "respectfulness": 1},
                 harm_note="This is a much longer note that exceeds fifty characters and should be captured as a quote"),
        ]
        quotes = extract_quotes(anns, min_length=50)
        assert len(quotes) == 1
        assert "longer note" in quotes[0]["quote"]


class TestSummaryTable:
    def test_produces_dataframe(self):
        df = summary_table(SAMPLE)
        assert len(df) > 0
        assert "Dimension" in df.columns
        assert "Group" in df.columns
        assert "n" in df.columns
