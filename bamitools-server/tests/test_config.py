import pathlib

from bamitools_server.config import _find_env_file


def test_find_env_file_returns_string():
    result = _find_env_file()
    assert isinstance(result, str)


def test_find_env_file_finds_root():
    result = pathlib.Path(_find_env_file())
    assert result.name == ".env"
    assert result.is_file()
