import importlib.machinery
import importlib.util
import operator
import os
import pathlib
import sys
import types
import warnings

from typing import Any, Optional


if sys.version_info >= (3, 10):
    import importlib.metadata as importlib_metadata
    import importlib.resources as importlib_resources
else:
    import importlib_metadata
    import importlib_resources


def find_spec_no_exec(name: str) -> Optional[importlib.machinery.ModuleSpec]:
    """Find the spec for a module, without changing the import state.

    Similar to importlib.util.find_spec, but it that imports the module parents,
    this function does not trigger any import.
    """
    if name in sys.modules:
        return sys.modules[name].__spec__

    # Find parent spec, and get the parent search path
    if parent_name := name.rpartition('.')[0]:
        if not (parent_spec := find_spec_no_exec(parent_name)):
            return None
        # The __path__ attribute of a module may be dependent on its parent's
        # __path__, requiring the parent to be in sys.modules.
        #
        # This is the case, for eg., for namespace packages.
        # See https://github.com/python/cpython/blob/bcee1c322115c581da27600f2ae55e5439c027eb/Lib/importlib/_bootstrap_external.py#L1380-L1382
        #
        # To avoid having to place the parents in sys.modules, in order to be
        # able to access their __path__, we use spec.submodule_search_locations
        # instead.
        path = parent_spec.submodule_search_locations
    else:
        path = None

    # Search sys.meta_path finders
    for finder in sys.meta_path:
        if not hasattr(finder, 'find_spec'):
            continue
        if spec := finder.find_spec(name, path, None):
            return spec

    return None


def import_module_no_exec(name: str) -> types.ModuleType:
    """Return a module object with all the module attributes set, but without executing it.

    find_spec_no_exec is used instead of importlib.util.find_spec, to avoid
    the parent modules being imported as a side effect.
    """
    if name in sys.modules:
        return sys.modules[name]
    # Find module spec
    spec = find_spec_no_exec(name)
    if not spec:
        msg = f'No module named {name!r}'
        raise ModuleNotFoundError(msg)
    # Create module object without executing
    return importlib.util.module_from_spec(spec)


class EntryPoint:
    def __init__(self, entrypoint: importlib_metadata.EntryPoint) -> None:
        self._ep = entrypoint

    @property
    def name(self) -> str:
        return self._ep.name

    @property
    def value(self) -> str:
        return self._ep.value

    @property
    def group(self) -> str:
        return self._ep.group

    @property
    def dist(self) -> Optional[importlib_metadata.Distribution]:
        return self._ep.dist

    @property
    def path(self) -> str:
        try:
            return self._resolve_via_import_system()
        except Exception as e:
            msg = f'Failed to resolve the entrypoint path via the import system: {e!s}'
            warnings.warn(PathWarning(msg, self), stacklevel=2)
        # Fallback method
        return self._resolve_via_translation()

    def _resolve_via_import_system(self) -> str:
        module = import_module_no_exec(self.value)
        traversable = importlib_resources.files(module)
        return os.fsdecode(os.fspath(traversable))

    def _resolve_via_translation(self) -> str:
        assert self.dist
        subpath = pathlib.PurePath(*self.value.split('.'))
        dist_path = self.dist.locate_file(subpath)
        assert isinstance(dist_path, os.PathLike)
        return os.fsdecode(os.fspath(dist_path))


def entry_points(**select_params: Any) -> list[EntryPoint]:
    original_eps = importlib_metadata.entry_points(**select_params)
    our_eps = map(EntryPoint, original_eps)
    valid_eps = filter(operator.attrgetter('path'), our_eps)
    return sorted(valid_eps, key=operator.attrgetter('name'))


class PathWarning(Warning):
    def __init__(self, message: str, entrypoint: EntryPoint) -> None:
        self._message = message
        self._entrypoint = entrypoint

    def __str__(self) -> str:
        assert self._entrypoint.dist
        return f'{self._message}\n- Entrypoint: {self._entrypoint}\n- Distribution: {self._distribution_info()}\n'

    def _distribution_info(self) -> str:
        assert self._entrypoint.dist
        info = f'{self._entrypoint.dist.name}-{self._entrypoint.dist.version}'
        if metadata_path := self._find_metadata_path():
            info += f' at {metadata_path!r}'
        return info

    def _find_metadata_path(self) -> Optional[str]:
        assert self._entrypoint.dist
        try:
            dist_root = self._entrypoint.dist.locate_file('')
        except NotImplementedError:
            return None

        for file in self._entrypoint.dist.files or []:
            if file.parts[0].endswith('.dist-info'):
                return str(dist_root / file.parts[0])
        return None
