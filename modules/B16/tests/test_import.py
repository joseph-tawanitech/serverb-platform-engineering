from src.app import app


def test_app_import():
    assert app.title == "Server B B16 AI-SRE Operations Console"
    assert app.version == "0.1.0"
