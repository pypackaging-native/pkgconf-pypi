import sys

import pytest

import pkgconf._path_entrypoints


def test_cleanup_isolated_contexts_closes_subinterpreter():
    if sys.version_info < (3, 14):
        pytest.skip('subinterpreters require Python 3.14+')

    assert pkgconf._path_entrypoints.run_in_subinterpreter(str, 'ok') == 'ok'

    pkgconf._path_entrypoints._cleanup_isolated_contexts()

    assert pkgconf._path_entrypoints._subinterpreter is None
