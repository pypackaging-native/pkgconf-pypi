import importlib.metadata
import os
import sys

import pytest

import pkgconf._path_entrypoints


@pytest.mark.parametrize('alias_first', [False, True])
@pytest.mark.parametrize('alias_type', ['dot', 'symlink'])
def test_unique_paths_preserves_first_spelling(tmp_path, alias_first, alias_type):
    directory = tmp_path / 'directory'
    directory.mkdir()
    other = tmp_path / 'other'
    other.mkdir()
    if alias_type == 'symlink':
        alias_path = tmp_path / 'alias'
        try:
            alias_path.symlink_to(directory, target_is_directory=True)
        except OSError as exc:
            pytest.skip(f'Directory symlinks unavailable: {exc}')
        alias = str(alias_path)
    else:
        alias = str(directory) + os.sep + '.'
    first, duplicate = (alias, str(directory)) if alias_first else (str(directory), alias)

    paths = pkgconf._path_entrypoints.unique_paths([first, str(other), duplicate, first, str(other)])

    assert paths == [first, str(other)]


def test_entrypoint_paths_translation_fallback(tmp_path):
    metadata = tmp_path / 'missing-1.0.dist-info'
    metadata.mkdir()
    (metadata / 'METADATA').write_text('Name: missing\nVersion: 1.0\n')
    (metadata / 'entry_points.txt').write_text('[pkg_config]\nmissing = pkgconf_missing_package.pcfiles\n')
    dist = importlib.metadata.Distribution.at(metadata)
    entrypoint = pkgconf._path_entrypoints.EntryPoint(next(iter(dist.entry_points)))

    with pytest.warns(pkgconf._path_entrypoints.PathWarning):
        paths = entrypoint.paths

    assert paths == [str(tmp_path / 'pkgconf_missing_package' / 'pcfiles')]


def test_cleanup_isolated_contexts_closes_subinterpreter():
    if sys.version_info < (3, 14):
        pytest.skip('subinterpreters require Python 3.14+')

    assert pkgconf._path_entrypoints.run_in_subinterpreter(str, 'ok') == 'ok'

    pkgconf._path_entrypoints._cleanup_isolated_contexts()

    assert pkgconf._path_entrypoints._subinterpreter is None
