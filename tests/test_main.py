import json

import pytest

from context import reporchestrator


def test_main_choke_invalid_json():
    with pytest.raises(json.JSONDecodeError, match=r"Extra data: line 1 column 4 .*"):
        _ = reporchestrator.main(["-1 invalid_json"])


def test_main_choke_invalid_model():
    invalid_model = {
        "repo_dir": ''  # Invalid folder name
    }
    with pytest.raises(ValueError, match=r"empty repo_dir.*"):
        _ = reporchestrator.main([json.dumps(invalid_model)])
