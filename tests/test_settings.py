from app.config.settings import Settings


def test_settings_loads_printer_config() -> None:
    settings = Settings()
    assert settings.printer_type == "Argox"
    assert settings.copies >= 1
    assert settings.paper_width >= 1
