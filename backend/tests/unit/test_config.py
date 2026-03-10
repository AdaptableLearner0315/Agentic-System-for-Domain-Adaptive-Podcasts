"""
Unit tests for application configuration.

Tests CORS configuration, settings validation, and environment handling.
"""

import pytest
from app.config import Settings, get_settings


class TestCorsConfiguration:
    """Tests for CORS origin configuration."""

    def test_cors_origins_includes_common_dev_ports(self):
        """CORS should allow common development ports (3000-3010)."""
        settings = Settings()
        origins = settings.cors_origins_list

        # Test commonly used Next.js/React dev ports
        common_ports = [3000, 3001, 3002, 3003, 3004, 3005]
        for port in common_ports:
            assert f"http://localhost:{port}" in origins, (
                f"Port {port} should be allowed - Next.js falls back to higher ports when lower ones are in use"
            )
            assert f"http://127.0.0.1:{port}" in origins, (
                f"127.0.0.1:{port} should also be allowed for localhost variants"
            )

    def test_cors_origins_covers_port_range(self):
        """CORS should cover full port range 3000-3010 for dev flexibility."""
        settings = Settings()
        origins = settings.cors_origins_list

        # Verify all ports in range are covered
        for port in range(3000, 3011):
            localhost_origin = f"http://localhost:{port}"
            ip_origin = f"http://127.0.0.1:{port}"

            assert localhost_origin in origins, f"Missing {localhost_origin}"
            assert ip_origin in origins, f"Missing {ip_origin}"

    def test_cors_origins_is_list(self):
        """cors_origins_list should return a proper list."""
        settings = Settings()
        origins = settings.cors_origins_list

        assert isinstance(origins, list)
        assert len(origins) > 0
        assert all(isinstance(o, str) for o in origins)

    def test_cors_origins_no_trailing_whitespace(self):
        """CORS origins should not have trailing whitespace."""
        settings = Settings()
        origins = settings.cors_origins_list

        for origin in origins:
            assert origin == origin.strip(), f"Origin '{origin}' has whitespace"

    def test_cors_origins_valid_urls(self):
        """All CORS origins should be valid HTTP URLs."""
        settings = Settings()
        origins = settings.cors_origins_list

        for origin in origins:
            assert origin.startswith("http://") or origin.startswith("https://"), (
                f"Origin '{origin}' should start with http:// or https://"
            )
            # Should not have trailing slash
            assert not origin.endswith("/"), (
                f"Origin '{origin}' should not have trailing slash"
            )

    def test_cors_can_be_overridden_via_env(self, monkeypatch):
        """CORS origins can be overridden via environment variable."""
        custom_origins = "http://example.com,http://test.com"
        monkeypatch.setenv("CORS_ORIGINS", custom_origins)

        # Clear cache and create new settings
        get_settings.cache_clear()
        settings = Settings()

        assert "http://example.com" in settings.cors_origins_list
        assert "http://test.com" in settings.cors_origins_list

        # Reset
        get_settings.cache_clear()


class TestSettingsDefaults:
    """Tests for default settings values."""

    def test_default_app_name(self):
        """Should have correct default app name."""
        settings = Settings()
        assert settings.app_name == "Nell Podcast API"

    def test_default_api_prefix(self):
        """Should have /api as default prefix."""
        settings = Settings()
        assert settings.api_prefix == "/api"

    def test_default_max_upload_size(self):
        """Should have reasonable default upload size."""
        settings = Settings()
        assert settings.max_upload_size_mb == 100
        assert settings.max_upload_size_bytes == 100 * 1024 * 1024

    def test_api_keys_validation(self):
        """Should report API key configuration status."""
        settings = Settings()
        key_status = settings.validate_api_keys()

        assert "fal_key" in key_status
        assert "anthropic_api_key" in key_status
        assert isinstance(key_status["fal_key"], bool)
        assert isinstance(key_status["anthropic_api_key"], bool)


class TestJobTimeouts:
    """Tests for job timeout configuration."""

    def test_normal_mode_timeout(self):
        """Normal mode should have shorter timeout."""
        settings = Settings()
        timeout = settings.get_job_timeout("normal")
        assert timeout == settings.normal_mode_timeout_seconds
        assert timeout < settings.pro_mode_timeout_seconds

    def test_pro_mode_timeout(self):
        """Pro mode should have longer timeout."""
        settings = Settings()
        timeout = settings.get_job_timeout("pro")
        assert timeout == settings.pro_mode_timeout_seconds

    def test_unknown_mode_defaults_to_normal(self):
        """Unknown mode should default to normal timeout."""
        settings = Settings()
        timeout = settings.get_job_timeout("unknown")
        assert timeout == settings.normal_mode_timeout_seconds
