import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("AI_PROVIDER", "gemini")
import pytest, app as appmod

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(appmod, "P", "gemini"); monkeypatch.setattr(appmod, "KEY", "")
    return appmod.app.test_client()
