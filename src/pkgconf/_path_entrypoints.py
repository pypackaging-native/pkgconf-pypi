import contextlib
import importlib.machinery
import importlib.metadata
import importlib.resources
import importlib.util
import operator
import os
import pathlib
import pickle
import sys
import types
import warnings

from collections.abc import Callable, Iterable
from typing import Any, ParamSpec, TypeVar

import pkgconf


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
    traversable = importlib.resources.files(module)
    if isinstance(traversable, os.PathLike):
        return os.fsdecode(os.fspath(traversable))
    # Give up :/
    msg = f'Unable to resolve the path for {name}'
    raise ValueError(msg)


# Helpers to run the import helpers isolated from the import state of the main process/interpreter

_subinterpreter = None


def run_in_subinterpreter(fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    """Run callable in a subinterpreter — using concurrent.interpreters."""
    assert sys.version_info >= (3, 14)

    import concurrent.interpreters

    global _subinterpreter

    if _subinterpreter is None:
        _subinterpreter = concurrent.interpreters.create()

    return _subinterpreter.call(fn, *args, **kwargs)


_worker = None
_WORKER_CODE = r"""
import sys, pickle

stdin, stdout = sys.stdin.buffer, sys.stdout.buffer

while True:
    try:
        length_data = stdin.read(4)
        if not length_data:
            break
        length = int.from_bytes(length_data, "big")
        payload = stdin.read(length)
        fn, args, kwargs = pickle.loads(payload)
        try:
            result = fn(*args, **kwargs)
            data = pickle.dumps((True, result))
        except Exception as e:
            data = pickle.dumps((False, e))
        stdout.write(len(data).to_bytes(4, "big"))
        stdout.write(data)
        stdout.flush()
    except Exception:
        break
"""


def _make_worker():
    """Start worker subprocess and assign callable to _worker."""
    global _worker
    import subprocess

    proc = subprocess.Popen(
        [sys.executable, '-u', '-c', _WORKER_CODE],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )

    def _worker_fn(fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        payload = pickle.dumps((fn, args, kwargs))
        length = len(payload).to_bytes(4, 'big')

        proc.stdin.write(length)
        proc.stdin.write(payload)
        proc.stdin.flush()

        length_data = proc.stdout.read(4)
        if not length_data:
            msg = 'Subprocess died'
            raise RuntimeError(msg)
        resp_length = int.from_bytes(length_data, 'big')
        data = proc.stdout.read(resp_length)
        ok, value = pickle.loads(data)

        if ok:
            return value
        else:
            raise value

    _worker = _worker_fn


def run_in_subprocess(fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    """Run callable in a subprocess."""
    if _worker is None:
        _make_worker()

    return _worker(fn, *args, **kwargs)


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
    def __init__(self, entrypoint: importlib.metadata.EntryPoint) -> None:
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
    def dist(self) -> importlib.metadata.Distribution | None:
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
    original_eps = importlib.metadata.entry_points(**select_params)
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

    def _find_metadata_path(self) -> str | None:
        assert self._entrypoint.dist
        try:
            dist_root = self._entrypoint.dist.locate_file('')
        except NotImplementedError:
            return None

        for file in self._entrypoint.dist.files or []:
            if file.parts[0].endswith('.dist-info'):
                return str(dist_root / file.parts[0])
        return None
