import sys
from unittest import mock

import pytest


def test_python_version_guard():
    with mock.patch.object(sys, 'version_info') as v_info:
        v_info.major = 2
        v_info.minor = 7
        del sys.modules["reporchestrator"]
        with pytest.raises(RuntimeError, match=r".*higher.*"):
            import reporchestrator


def test_import_guards():
    with mock.patch.dict(sys.modules, {'faker': None}):
        with pytest.raises(ImportError, match=r".*faker.*"):
            import reporchestrator


def test_import_git_guard():
    with mock.patch.dict(sys.modules, {'git': None}):
        with pytest.raises(ImportError, match=r".*gitpython.*"):
            import reporchestrator
