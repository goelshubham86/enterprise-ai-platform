"""Tests for the centralised Settings class.

Verifies that every setting has a usable default and that type coercion
from environment variables works correctly.  No GCP credentials required.
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, settings


class TestSettingsDefaults:
    """All defaults must be non-null and sensible without an .env file."""

    def test_singleton_is_settings_instance(self):
        assert isinstance(settings, Settings)

    def test_gcp_project_id_has_default(self):
        assert settings.gcp_project_id != ""

    def test_gcp_region_default(self):
        assert settings.gcp_region == "us-central1"

    def test_vertex_model_id_default(self):
        assert settings.vertex_model_id == "gemini-1.5-pro-002"

    def test_vertex_embedding_model_default(self):
        assert settings.vertex_embedding_model == "text-embedding-004"

    def test_chunk_size_is_positive(self):
        assert settings.chunk_size > 0

    def test_chunk_overlap_is_non_negative(self):
        assert settings.chunk_overlap >= 0

    def test_chunk_overlap_smaller_than_chunk_size(self):
        assert settings.chunk_overlap < settings.chunk_size

    def test_top_k_is_positive(self):
        assert settings.top_k > 0

    def test_cors_origins_is_list(self):
        assert isinstance(settings.cors_origins, list)
        assert len(settings.cors_origins) >= 1

    def test_log_level_is_valid(self):
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        assert settings.log_level.upper() in valid_levels


class TestSettingsEnvOverride:
    """Env-var overrides are applied correctly via pydantic-settings."""

    def test_override_chunk_size(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("CHUNK_SIZE", "256")
        s = Settings()
        assert s.chunk_size == 256

    def test_override_top_k(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("TOP_K", "10")
        s = Settings()
        assert s.top_k == 10

    def test_override_gcp_region(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("GCP_REGION", "europe-west1")
        s = Settings()
        assert s.gcp_region == "europe-west1"

    def test_cors_origins_parsed_from_json_list(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("CORS_ORIGINS", '["https://app.example.com"]')
        s = Settings()
        assert "https://app.example.com" in s.cors_origins
