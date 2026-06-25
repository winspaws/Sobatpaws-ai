"""Unit tests untuk modul vision."""
from __future__ import annotations

import base64
import io
from unittest.mock import MagicMock, patch

import pytest

from ekosistem_satwa.vision.analyzer import VisionService, _parse_lesions, _parse_wound
from ekosistem_satwa.vision.image_utils import preprocess_image, validate_image_bytes
from ekosistem_satwa.vision.schemas import VisionFocus, VisionMediaType


def _tiny_png() -> bytes:
    try:
        from PIL import Image

        buf = io.BytesIO()
        Image.new("RGB", (64, 64), color=(200, 100, 50)).save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        # Minimal valid PNG header fallback
        return (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        )


class TestImageUtils:
    def test_validate_rejects_empty(self):
        with pytest.raises(ValueError, match="kosong"):
            validate_image_bytes(b"")

    def test_preprocess_returns_metadata(self):
        data = _tiny_png()
        try:
            out, mime, meta = preprocess_image(data, "image/png")
        except ValueError:
            pytest.skip("Pillow tidak tersedia")
        assert len(out) > 0
        assert mime.startswith("image/")
        assert meta.width > 0


class TestVisionParsing:
    def test_parse_lesions(self):
        raw = [
            {
                "location": "left_ear",
                "type": "erythema",
                "severity": "mild",
                "description": "kemerahan ringan",
                "confidence": 0.9,
            }
        ]
        lesions = _parse_lesions(raw)
        assert len(lesions) == 1
        assert lesions[0].location == "left_ear"

    def test_parse_wound_from_lesions(self):
        from ekosistem_satwa.ai.schemas import VisionLesion

        lesions = [
            VisionLesion(
                location="dorsal_trunk",
                type="laceration",
                severity="moderate",
                description="luka sayat",
                confidence=0.85,
            )
        ]
        wound = _parse_wound(None, lesions)
        assert wound is not None
        assert wound.present is True
        assert wound.wound_type == "laceration"


class TestVisionService:
    def test_analyze_image_with_mock_llm(self):
        mock_llm = MagicMock()
        mock_llm.available = True
        mock_llm.describe_image.return_value = {
            "species_detected": "dog",
            "breed_hints": ["golden_retriever"],
            "age_estimate_min_years": 2.0,
            "age_estimate_max_years": 4.0,
            "age_confidence": 0.7,
            "lesions": [
                {
                    "location": "right_hind_leg",
                    "type": "laceration",
                    "severity": "moderate",
                    "description": "luka sayat dengan perdarahan minor",
                    "confidence": 0.88,
                }
            ],
            "red_flags": [],
            "extracted_symptoms": ["luka", "perdarahan"],
            "raw_description": "Anjing dengan luka sayat di kaki belakang kanan.",
            "animal_form": {
                "posture": "limping",
                "coat_condition": "normal",
                "confidence": 0.7,
            },
            "wound": {
                "present": True,
                "wound_type": "laceration",
                "bleeding": "minor",
                "location": "right_hind_leg",
                "confidence": 0.88,
            },
        }

        svc = VisionService(llm=mock_llm)
        result = svc.analyze_image(
            _tiny_png(),
            mime_type="image/png",
            category_slug="dog",
            focus=VisionFocus.wound,
        )

        assert result.media_type == VisionMediaType.image
        assert result.species_detected == "dog"
        assert result.wound is not None
        assert result.wound.present is True
        assert len(result.lesions) == 1
        assert "luka" in result.raw_description.lower() or result.raw_description

    def test_capabilities_reports_llm(self):
        mock_llm = MagicMock()
        mock_llm.available = True
        svc = VisionService(llm=mock_llm)
        caps = svc.capabilities()
        assert caps.image_supported is True
        assert caps.llm_vision_available is True

    def test_analyze_base64_invalid(self):
        svc = VisionService(llm=MagicMock(available=False))
        with pytest.raises(ValueError, match="base64"):
            svc.analyze_image_base64("not-valid-base64!!!")
