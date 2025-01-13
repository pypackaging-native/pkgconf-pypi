import contextlib
import importlib.util
import sys
import types

from typing import Any


class LazyModule(types.ModuleType):
    def __getattribute__(self, name: str) -> Any:
        with contextlib.suppress(AttributeError):
            return object.__getattribute__(self, name)
        # Undo patching — restore the original __getattribute__, __class__, and loader_state
        __spec__ = object.__getattribute__(self, '__spec__')
        object.__setattr__(self, '__class__', __spec__.loader_state['__class__'])
        object.__setattr__(self, '__getattribute__', __spec__.loader_state['__getattribute__'])
        __spec__.loader_state = __spec__.loader_state['loader_state']
        # Run the original __getattribute__
        return self.__getattribute__(name)


class LazyLoader(importlib.util.LazyLoader):
    """Custom type extending importlib.util.LazyLoader's capabilities.

    It uses the importlib.util.LazyLoader implementation, but provides a custom
    __getattribute__ that delays the execution when accessing types.ModuleType
    attributes (like __spec__, __path__, __file__, etc.).

    The original implementation triggers the module execution when accessing
    *any* attribute, even ones initialized in types.ModuleType. While it is
    highly discouraged to change any of these attributes during module
    execution, it is technically permitted, so the default LazyLoader
    implementation makes the decision to trigger the module execution on any
    attribute access. We don't care so much about that, so we make choice to
    allow attribute access to to existing pre-initilized attributes without
    executing the module.
    """

    def exec_module(self, module: types.ModuleType) -> None:
        # Run
        super().exec_module(module)
        # Get module.__spec__ using object.__getattribute__ to avoid triggering
        # the original __getattribute__, which will always execute the module.
        __spec__ = object.__getattribute__(module, '__spec__')
        # Save the original __getattribute__ and __class__
        __spec__.loader_state = {
            '__class__': object.__getattribute__(module, '__class__'),
            '__getattribute__': object.__getattribute__(module, '__getattribute__'),
            'loader_state': __spec__.loader_state,
        }
        # Replace __class__ so that attribute lookups use our __getattribute__
        module.__class__ = LazyModule


def import_module_no_exec(name: str) -> types.ModuleType:
    """Return a module object with all the module attributes set, but without executing it."""
    if name in sys.modules:
        return sys.modules[name]
    # Import parent without execution
    if parent := name.rpartition('.')[0]:
        import_module_no_exec(parent)
    # Find spec
    spec = importlib.util.find_spec(name)
    if not spec:
        msg = f'No module named {name!r}'
        raise ModuleNotFoundError(msg)
    # Create module object without executing
    module = importlib.util.module_from_spec(spec)
    # Make the module load lazily (only executes when an attribute is accessed)
    LazyLoader(spec.loader).create_module(module)
    # Save to sys.modules
    sys.modules[name] = module
    return module
