import contextlib
import importlib.machinery
import importlib.util
import operator
import os
import pathlib
import pickle
import sys
import textwrap
import types
import warnings

from collections.abc import Iterable
from typing import Any, Callable, Optional, ParamSpec, TypeVar

import pkgconf


if sys.version_info >= (3, 10):
    import importlib.metadata as importlib_metadata
    import importlib.resources as importlib_resources
else:
    import importlib_metadata
    import importlib_resources


P = ParamSpec('P')
T = TypeVar('T')


# Import system helpers


def import_module_no_exec(name: str) -> types.ModuleType:
    """Return a module object with all the module attributes set, but without executing it.

    WARNING: This places uninitialized modules in sys.modules.
    """
    if name in sys.modules:
        return sys.modules[name]
    # Import parent without execution
    if parent := name.rpartition('.')[0]:
        import_module_no_exec(parent)
    # Find module spec
    spec = importlib.util.find_spec(name)
    if not spec:
        msg = f'No module named {name!r}'
        raise ModuleNotFoundError(msg)
    # Create module object without executing, and save it sys.modules
    module = sys.modules[name] = importlib.util.module_from_spec(spec)
    return module


def module_path(name: str) -> str:
    """Resolve module name to file-system path.

    WARNING: This places uninitialized modules in sys.modules.
    """
    module = import_module_no_exec(name)
    # Check if submodule_search_locations is set on the spec.
    if module.__spec__.submodule_search_locations:
        # If it contains a single path, use it.
        if len(module.__spec__.submodule_search_locations) == 1:
            return module.__spec__.submodule_search_locations[0]
    # Traversables often implement __fspath__, attempt to use it.
    traversable = importlib_resources.files(module)
    if isinstance(traversable, os.PathLike):
        return os.fsdecode(os.fspath(traversable))
    # Give up :/
    msg = f'Unable to resolve the path for {name}'
    raise ValueError(msg)


# Helpers to run the import helpers isolated from the import state of the main process/interpreter


def run_in_subinterpreter(fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    """Run callable in a subinterpreter — using concurrent.interpreters."""
    assert sys.version_info >= (3, 14)

    import concurrent.interpreters

    with contextlib.closing(concurrent.interpreters.create()) as ip:
        return ip.call(fn, *args, **kwargs)


def run_in_subprocess(fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    """Run callable in a subprocess."""
    import subprocess

    pickled_call_tuple = pickle.dumps((fn, args, kwargs))
    process_cmd = textwrap.dedent(f"""
        import pickle, sys

        fn, args, kwargs = pickle.loads({pickled_call_tuple})
        value = fn(*args, **kwargs)
        sys.stdout.buffer.write(
            pickle.dumps(value)
        )
    """)
    pickled_value = subprocess.run(
        [sys.executable, '-c', process_cmd],
        check=True,
        capture_output=True,
    ).stdout
    return pickle.loads(pickled_value)


def run_in_isolated_context(fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    try:
        if sys.version_info >= (3, 14):
            return run_in_subinterpreter(fn, *args, **kwargs)
    except Exception:
        pkgconf._LOGGER.exception(f'Failed to run {fn} in subinterpreter, falling back to subprocess')
    return run_in_subprocess(fn, *args, **kwargs)


@contextlib.contextmanager
def replace_sys_modules() -> Iterable[None]:
    original = sys.modules
    sys.modules = original.copy()
    try:
        yield
    finally:
        sys.modules = original


# Entrypoint helpers


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
        except Exception:
            msg = 'Failed to resolve the entrypoint path via the import system (see log for details)'
            pkgconf._LOGGER.exception(msg)
            warnings.warn(PathWarning(msg, self), stacklevel=2)
        # Fallback method
        return self._resolve_via_translation()

    def _resolve_via_import_system(self) -> str:
        # module_path is not safe to run directly in the execution context, as
        # it alters the import state, so try to run it in an isolated context.
        try:
            return run_in_isolated_context(module_path, self.value)
        except Exception:
            pkgconf._LOGGER.exception('Failed to run module_path in isolated context')
        # Fallback to running in the current context, but try to save and
        # restore the original import state.
        with replace_sys_modules():
            return module_path(self.value)

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
        super().__init__(message)
        self._entrypoint = entrypoint
        self._logger = pkgconf._LOGGER.getChild(self.__class__.__name__)
        self._logger.warning(
            message,
            extra={
                'entrypoint': self._entrypoint,
                'distribution': self._distribution_info(),
            },
        )

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
