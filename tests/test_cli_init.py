"""Tests for the interactive init command."""

from __future__ import annotations

import os

import yaml

import fluff_cutter.config as config_module
from fluff_cutter import cli


def _mock_user_config(tmp_path, monkeypatch):
    config_dir = tmp_path / ".fluff-cutter"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    monkeypatch.setattr(config_module, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
    monkeypatch.setattr(config_module, "OLD_CONFIG_DIR", tmp_path / "old-config")
    monkeypatch.setattr(config_module, "OLD_CONFIG_FILE", tmp_path / "old-config" / "config.json")
    return config_file


def test_init_only_prompts_for_selected_provider(tmp_path, monkeypatch, capsys):
    config_file = _mock_user_config(tmp_path, monkeypatch)
    original = {
        "openai_api_key": "sk-openai",
        "anthropic_api_key": "sk-anthropic",
        "openrouter_api_key": "sk-openrouter",
        "openai_model": "gpt-custom",
        "anthropic_model": "claude-custom",
        "default_provider": "openrouter",
        "default_wiki_root": "/tmp/wiki",
    }
    config_file.write_text(yaml.safe_dump(original), encoding="utf-8")

    prompts = []

    def fake_input(prompt):
        prompts.append(prompt)
        return ""

    def fake_getpass(prompt):
        prompts.append(prompt)
        return ""

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr(cli.getpass, "getpass", fake_getpass)
    monkeypatch.setattr(cli.sys, "argv", ["fluff-cutter", "init"])

    cli.main()

    assert prompts == [
        "Provider [openrouter]: ",
        "OpenRouter API Key [sk-o...uter]: ",
        "OpenRouter model [anthropic/claude-sonnet-4-5]: ",
    ]
    saved = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    assert saved == original

    output = capsys.readouterr().out
    assert "OpenAI API Key" not in output
    assert "Anthropic API Key" not in output
    assert "Default provider: openrouter" in output


def test_init_configures_one_new_provider(tmp_path, monkeypatch):
    config_file = _mock_user_config(tmp_path, monkeypatch)
    answers = iter(["openrouter", ""])

    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    monkeypatch.setattr(cli.getpass, "getpass", lambda _prompt: "sk-new-openrouter")
    monkeypatch.setattr(cli.sys, "argv", ["fluff-cutter", "init"])

    cli.main()

    assert yaml.safe_load(config_file.read_text(encoding="utf-8")) == {
        "openrouter_api_key": "sk-new-openrouter",
        "default_provider": "openrouter",
    }


def test_init_retries_invalid_provider(tmp_path, monkeypatch, capsys):
    config_file = _mock_user_config(tmp_path, monkeypatch)
    answers = iter(["invalid", "openai", ""])

    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    monkeypatch.setattr(cli.getpass, "getpass", lambda _prompt: "sk-openai")
    monkeypatch.setattr(cli.sys, "argv", ["fluff-cutter", "init"])

    cli.main()

    assert "Please choose from: openai, anthropic, openrouter" in capsys.readouterr().out
    assert yaml.safe_load(config_file.read_text(encoding="utf-8")) == {
        "openai_api_key": "sk-openai",
        "default_provider": "openai",
    }


def test_init_does_not_persist_environment_key(tmp_path, monkeypatch, capsys):
    config_file = _mock_user_config(tmp_path, monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-environment")
    answers = iter(["openai", ""])

    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: "" if "API Key" in prompt else "")
    monkeypatch.setattr(cli.sys, "argv", ["fluff-cutter", "init"])

    cli.main()

    saved = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    assert saved == {"default_provider": "openai"}
    assert "sk-from-environment" not in config_file.read_text(encoding="utf-8")
    assert "from the environment (not saved)" in capsys.readouterr().out
    assert os.environ["OPENAI_API_KEY"] == "sk-from-environment"
