from unittest import mock
import configparser
import json
import os

import pytest

from context import reporchestrator


def test_create_repository():
    reporchestrator.create_repository({"repo_dir": ""})


def test_activate_model():
    def change_me():
        return -1
    d = reporchestrator.activate_model({"fake": change_me})
    assert d["fake"] == -1


def test_pairs_to_actors():
    import git
    pairs = [("a", "b")]
    actors = reporchestrator.pairs_to_actors(pairs)
    assert actors[0] == git.Actor("a", "b")


def test_mixin():
    internal_random_seed = 22
    c = reporchestrator.mixin()
    assert c["random_seed"] == internal_random_seed


def test_mixin_string():
    argument = '{"foo": "bar"}'
    c = reporchestrator.mixin([argument])
    assert c["foo"] == "bar"
    assert c == dict(foo="bar")


def test_mixin_not_found():
    c = reporchestrator.mixin("non-existing-file.really")
    assert c == {}


def test_mixin_string_developer_data():
    import git
    argument = '{"developer_data": [["a", "b"]]}'
    c = reporchestrator.mixin([argument])
    assert c["developer_data"] == [["a", "b"]]
    assert set(c.keys()) == {"developer_data", "developers"}
    assert c["developers"][0] == git.Actor("a", "b")


def test_defaults_non_file():
    with pytest.raises(json.JSONDecodeError, match=r"Expecting value: line 1 column 1 .*"):
        _ = reporchestrator.defaults(["non-existing-file.really"])


def test_defaults_empty_list():
    internal_random_seed = 22
    c = reporchestrator.defaults([])
    assert isinstance(c, dict)
    assert c["random_seed"] == internal_random_seed


def test_defaults():
    internal_random_seed = 22
    c = reporchestrator.defaults()
    assert isinstance(c, dict)
    assert c["random_seed"] == internal_random_seed


def test_repo_tree_removal(tmpdir):
    """real rmdir"""
    a_dir = tmpdir.join("foo")
    os.mkdir(a_dir)
    assert os.path.isdir(a_dir), "before removal"
    reporchestrator.create_repository({"repo_dir": a_dir})
    assert os.path.isdir(a_dir), "after removal and re-init"


def test_repo_folder_init(tmpdir):
    """real - .git/config"""
    a_dir = tmpdir.join("foo")
    reporchestrator.create_repository({"repo_dir": a_dir})

    assert os.path.isdir(a_dir)
    git_config_path = a_dir.join(".git", "config")
    assert os.path.isfile(git_config_path)
    git_config = configparser.ConfigParser()
    git_config.read(git_config_path)
    core_section = "core"
    assert core_section in git_config
    assert git_config.get(core_section, "bare", fallback=None) == "false"


@mock.patch('os.path.isfile')
def test_repo_init_virtual(if_mock):
    a_file = "faked-file.really"
    if_mock.return_value = True
    some_json_object = json.dumps({"a": "b"})
    mock_open = mock.mock_open(read_data=some_json_object)

    with mock.patch('builtins.open', mock_open):
        try:
            c = reporchestrator.mixin([a_file])
        except IOError as err:
            c = err

    if_mock.assert_called_with(a_file)
    assert if_mock.return_value is True
    assert c == json.loads(some_json_object)


def test_json_from_file():
    a_file = "faked-file.really"
    some_json_object = json.dumps({"a": "b"})
    mock_open = mock.mock_open(read_data=some_json_object)
    with mock.patch('builtins.open', mock_open):
        d = reporchestrator.json_from_file(a_file)

    assert d is not None
    assert d == json.loads(some_json_object)


def test_unknown_developer_strategy():
    invalid_strategy_in_model = {
        "repo_dir": 'DO_NOT_CREATE_THIS_FOLDER',
        "developer_strategy": "unknown-strategy"
    }
    invalid_strategy_in_ok_json = json.dumps(invalid_strategy_in_model)
    with pytest.raises(ValueError, match=r".*'unknown-strategy'.*"):
        _ = reporchestrator.defaults([invalid_strategy_in_ok_json])
