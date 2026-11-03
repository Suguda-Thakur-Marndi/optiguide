from app.core.config import Settings


def test_settings_defaults():
    settings = Settings()
    assert settings.APP_NAME == "OptiGuide"
    assert settings.APP_VERSION == "1.0.0"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.LOG_LEVEL == "INFO"


def test_settings_cors_origins_json_list():
    settings = Settings(CORS_ORIGINS='["http://localhost:3000","http://example.com"]')
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "http://example.com" in settings.CORS_ORIGINS


def test_settings_cors_origins_comma_separated():
    settings = Settings(CORS_ORIGINS="http://localhost:3000, http://test.org")
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "http://test.org" in settings.CORS_ORIGINS


def test_settings_custom_values():
    settings = Settings(
        APP_NAME="CustomOptiGuide",
        APP_ENV="staging",
        APP_DEBUG=True,
    )
    assert settings.APP_NAME == "CustomOptiGuide"
    assert settings.APP_ENV == "staging"
    assert settings.APP_DEBUG is True
