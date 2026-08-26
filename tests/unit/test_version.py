"""Testes da leitura da versão da aplicação em `utils/version.py`."""

import utils.version as version_module
from utils.version import FALLBACK_VERSION, get_app_version


def _point_to(tmp_path, monkeypatch, content=None):
    """Aponta o módulo para um `.version` temporário (ou inexistente)."""
    version_file = tmp_path / ".version"
    if content is not None:
        version_file.write_text(content)
    monkeypatch.setattr(version_module, "_VERSION_FILE", str(version_file))


def test_missing_file_falls_back(tmp_path, monkeypatch):
    _point_to(tmp_path, monkeypatch)
    assert get_app_version() == FALLBACK_VERSION


def test_empty_file_falls_back(tmp_path, monkeypatch):
    _point_to(tmp_path, monkeypatch, "  \n")
    assert get_app_version() == FALLBACK_VERSION


def test_plain_version_is_read_as_is(tmp_path, monkeypatch):
    _point_to(tmp_path, monkeypatch, "v1.0.0\n")
    assert get_app_version() == "v1.0.0"


def test_build_suffix_is_discarded(tmp_path, monkeypatch):
    _point_to(tmp_path, monkeypatch, "v1.2.3-rc1-dirty")
    assert get_app_version() == "v1.2.3"
