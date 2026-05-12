import json

from devlog import config


def test_load_config_returns_empty_dict_when_missing_or_invalid(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(config, "_CONFIG_PATH", config_path)

    assert config.load_config() == {}

    config_path.write_text("{")
    assert config.load_config() == {}


def test_save_config_creates_parent_directory_and_loads_json(tmp_path, monkeypatch):
    config_path = tmp_path / "nested" / "config.json"
    monkeypatch.setattr(config, "_CONFIG_PATH", config_path)

    config.save_config({"portfolio": "local"})

    assert json.loads(config_path.read_text()) == {"portfolio": "local"}
    assert config.load_config() == {"portfolio": "local"}
