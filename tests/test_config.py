from unittest import mock

import pytest

from context import reporchestrator


def test_create_repository():
    reporchestrator.create_repository({"repo_dir": ""})


def test_activate_model():
    def change_me():
        return 42
    d = reporchestrator.activate_model({"fake": change_me})
    assert d["fake"] == 42


def test_pairs_to_actors():
    import git
    pairs = [("a", "b")]
    actors = reporchestrator.pairs_to_actors(pairs)
    assert actors[0] == git.Actor("a", "b")


def test_mixin():
    c = reporchestrator.mixin()
    assert c["random_seed"] == 22


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
    import json
    with pytest.raises(json.JSONDecodeError, match=r"Expecting value: line 1 column 1 .*"):
        _ = reporchestrator.defaults(["non-existing-file.really"])


def test_defaults_empty_list():
    c = reporchestrator.defaults([])
    assert isinstance(c, dict)
    assert c["random_seed"] == 22


def test_defaults():
    c = reporchestrator.defaults()
    assert isinstance(c, dict)
    assert c["random_seed"] == 22


@mock.patch('shutil.rmtree')
def test_repo_tree_removal(rm_mock):
    a_dir = "foo"
    rm_mock.return_value = 'REMOVED'

    reporchestrator.create_repository({"repo_dir": a_dir})

    rm_mock.assert_called_with(a_dir, ignore_errors=True)
    assert rm_mock.return_value == 'REMOVED'


@mock.patch('os.path.isfile')
def test_repo_init(if_mock):
    import json
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
    import json
    a_file = "faked-file.really"
    some_json_object = json.dumps({"a": "b"})
    mock_open = mock.mock_open(read_data=some_json_object)
    with mock.patch('builtins.open', mock_open):
        d = reporchestrator.json_from_file(a_file)

    assert d is not None
    assert d == json.loads(some_json_object)


def test_unknown_developer_strategy():
    with pytest.raises(ValueError, match=r".*'unknown-strategy'.*"):
        _ = reporchestrator.defaults(['{"developer_strategy": "unknown-strategy"}'])
