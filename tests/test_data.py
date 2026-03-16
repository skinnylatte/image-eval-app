"""Tests for the data layer."""

import json
import os
import tempfile
from types import SimpleNamespace
from unittest import mock

import pytest

# Patch DATA_DIR before importing data module
_tmpdir = tempfile.mkdtemp()

with mock.patch.dict(os.environ, {}):
    import data as data_mod

    # Override paths to use temp directory
    data_mod.DATA_DIR = _tmpdir
    data_mod.IMAGES_DIR = os.path.join(_tmpdir, "images")
    os.makedirs(data_mod.IMAGES_DIR, exist_ok=True)


def _mock_session_state(**kwargs):
    """Create a mock st module whose session_state supports attribute access."""
    m = mock.MagicMock()
    m.session_state = SimpleNamespace(**kwargs)
    return m


class TestAnonymousId:
    def test_format(self):
        aid = data_mod.generate_anonymous_id()
        assert aid.startswith("P-")
        assert len(aid) == 10  # P- + 8 hex chars

    def test_unique(self):
        ids = {data_mod.generate_anonymous_id() for _ in range(100)}
        assert len(ids) == 100


class TestIdentityMapping:
    def test_save_and_load(self):
        data_mod.save_identity_mapping("P-testtest", "Alice", "Pakistan")
        path = os.path.join(data_mod.DATA_DIR, "_id_P-testtest.json")
        mapping = data_mod._read_json(path, default={})
        assert mapping["name"] == "Alice"
        assert mapping["background"] == "Pakistan"
        assert "registered_at" in mapping

    def test_multiple_participants_no_race(self):
        data_mod.save_identity_mapping("P-aaa10001", "Bob", "Iran")
        data_mod.save_identity_mapping("P-aaa20002", "Carol", "Turkey")
        bob = data_mod._read_json(os.path.join(data_mod.DATA_DIR, "_id_P-aaa10001.json"), default={})
        carol = data_mod._read_json(os.path.join(data_mod.DATA_DIR, "_id_P-aaa20002.json"), default={})
        assert bob["name"] == "Bob"
        assert carol["name"] == "Carol"


def _set_session(pid="P-test", background="Pakistan"):
    """Set data_mod.st to a mock with attribute-accessible session_state."""
    data_mod.st = _mock_session_state(participant_id=pid, participant_background=background)


class TestBuildAnnotation:
    def test_required_fields(self):
        _set_session("P-xxxx", "Pakistan")

        ann = data_mod.build_annotation(
            prompt="A doctor",
            category="profession",
            model_key="dalle",
            model_name="DALL-E 3",
            prompt_type="shared",
            status="success",
            scores={"authenticity": 3, "diversity": 4, "respectfulness": 5},
            expectation="Expected diversity",
            authenticity_note="Felt authentic",
            harm_note="No harm noted",
        )

        assert ann["participant_id"] == "P-xxxx"
        assert ann["background"] == "Pakistan"
        assert ann["prompt"] == "A doctor"
        assert ann["model"] == "dalle"
        assert ann["model_name"] == "DALL-E 3"
        assert ann["prompt_type"] == "shared"
        assert ann["status"] == "success"
        assert ann["scores"]["authenticity"] == 3
        assert ann["expectation"] == "Expected diversity"
        assert ann["refusal_note"] is None
        assert "timestamp" in ann

    def test_refusal(self):
        _set_session("P-yyyy", "Iran")

        ann = data_mod.build_annotation(
            prompt="A protest",
            category="sensitive",
            model_key="dalle",
            model_name="DALL-E 3",
            prompt_type="free",
            status="refused",
            refusal_note="Erasure of political expression",
        )

        assert ann["status"] == "refused"
        assert ann["scores"] is None
        assert ann["refusal_note"] == "Erasure of political expression"
        assert ann["expectation"] is None


class TestSaveLoadAnnotations:
    def test_roundtrip(self):
        pid = "P-rt01"
        _set_session(pid, "Egypt")

        ann = data_mod.build_annotation(
            prompt="Test prompt",
            category="profession",
            model_key="stable_diffusion",
            model_name="Stable Diffusion XL",
            prompt_type="free",
            status="success",
            scores={"authenticity": 2, "diversity": 1, "respectfulness": 3},
        )

        data_mod.save_annotation(ann)
        loaded = data_mod.load_annotations(pid)

        assert len(loaded) == 1
        assert loaded[0]["prompt"] == "Test prompt"
        assert loaded[0]["scores"]["diversity"] == 1

    def test_append(self):
        pid = "P-ap01"
        _set_session(pid, "Turkey")

        for i in range(3):
            ann = data_mod.build_annotation(
                prompt=f"Prompt {i}",
                category="cultural",
                model_key="dalle",
                model_name="DALL-E 3",
                prompt_type="shared",
                status="success",
                scores={"authenticity": i + 1, "diversity": i + 1, "respectfulness": i + 1},
            )
            data_mod.save_annotation(ann)

        loaded = data_mod.load_annotations(pid)
        assert len(loaded) == 3

    def test_load_nonexistent(self):
        loaded = data_mod.load_annotations("P-nope")
        assert loaded == []


class TestSaveImageToDisk:
    def test_writes_file(self):
        path = data_mod.save_image_to_disk(b"fake-png-bytes", "P-img1", 0, "dalle", 0)
        assert os.path.exists(path)
        with open(path, "rb") as f:
            assert f.read() == b"fake-png-bytes"


class TestGenerateImages:
    def test_placeholder_returns_success(self):
        result = data_mod.generate_images("A doctor", "dalle", 4)
        assert result["status"] == "success"
        assert len(result["images"]) == 4
        assert result["message"] is None
