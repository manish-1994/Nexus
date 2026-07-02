from config import settings


def test_settings_loaded():
    """Test that settings are loaded correctly."""
    assert settings.project_name == "NEXUS V3"
    assert settings.version == "0.1.0"
    assert settings.api_v1_prefix == "/api/v1"


def test_cors_origins():
    """Test CORS origins parsing."""
    origins = settings.cors_origins_list
    assert isinstance(origins, list)
    assert len(origins) > 0
