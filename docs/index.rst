************
pkgconf-pypi
************

The `pkgconf PyPI package`_ provides a pre-built pkgconf_ binary, as well as an
optional integration layer for Python packages.

It provides the following executables:

.. list-table::

    * - ``pkgconf``/``pkg-config``
      - These executables provide the "vanilla" ``pkgconf`` functionality, with
        a limitation — they don't have any knowledge of the system .pc files.
        This means, they rely on the user setting ``PKG_CONFIG_PATH`` (or using
        the equivalent ``--with-path`` CLI option).

        Setting the the ``FORCE_PKGCONF_PYPI`` environment variable forces them
        to behave the same as ``pkgconf-pypi``.

    * - ``pkgconf-pypi``
      - This is a ``pkgconf`` wrapper that integrates with the Python packaging
        system, as documented below. It enables Python packages to add locations
        to the search path. On lookup failures, it tries to fallback to the
        system ``pkgconf``/``pkg-config`` executables. Please refer to the
        documentation below for the full behavior details.

.. versionchanged:: 2.5.1-2

    Following feedback from real-world usage of this package, the Python
    integration layer was removed from the ``pkgconf``/``pkg-config``
    executables, and moved to a new ``pkgconf-pypi`` executable.

    For backwards compatibility, or in scenarios where it is not possible to
    specify the ``pkg-config`` executable name to build tools, the old behavior
    can be enabled by setting the ``FORCE_PKGCONF_PYPI`` environment variable.

Python package integration
==========================

Using the integration layer, Python packages can register their own pkg-config
paths, which will be searched by the ``pkgconf-pypi`` executable shipped by this
package.

Registering ``pkg-config`` paths
--------------------------------

You can register search paths via the ``pkg_config`` entrypoint_ group. You
should create an entry that points to the Python module which contains your
``.pc`` files. The name of the entrypoint_ does not matter.

.. dropdown:: Example

    Using our header-only-library_ example package.

    .. code-block:: shell

        $ tree
        .
        ├── example
        │   ├── include
        │   │   └── example.h
        │   └── pkgconf
        │       └── example.pc
        └── pyproject.toml

        4 directories, 3 files

    Here, we have our pkg-config file in ``example/pkgconf```, so we need to create
    an entrypoint_ for the module ``example.pkgconf``.

    .. literalinclude:: ../examples/header-only-library/pyproject.toml
        :language: toml
        :linenos:
        :emphasize-lines: 12-13
        :caption: pyproject.toml

    And in our ``example.pc`` file, we use ``${pcfiledir}`` to make it
    relocatable.

    .. literalinclude:: ../examples/header-only-library/example/pkgconf/example.pc
        :linenos:
        :emphasize-lines: 1
        :caption: example.pc

Package search path
-------------------

When you run the ``pkgconf-pypi`` executable provided by this package, the
``PKG_CONFIG_PATH`` environment variable will be set so that it can find the .pc
files registered by the ``pkg-config`` entrypoints_. If the ``PKG_CONFIG_PATH``
environment variable is already set, the locations registered by Python packages
will be appended.

If ``pkgconf-pypi`` cannot find a package, by default it will fallback to the
system ``pkgconf``/``pkg-config``, which may find packages present on the
system. To disable this behavior, set the ``PKGCONF_PYPI_EMBEDDED_ONLY=1``
environment variable.

To enable debug output to ``syserr``, set ``PYPI_PKGCONF_DEBUG=1``.

API
===

.. automodule:: pkgconf
   :members:
   :undoc-members:
   :show-inheritance:


.. _pkgconf PyPI package: https://pypi.org/project/pkgconf/
.. _pkgconf: https://github.com/pkgconf/pkgconf
.. _entrypoint: https://packaging.python.org/en/latest/specifications/entry-points
.. _entrypoints: https://packaging.python.org/en/latest/specifications/entry-points
.. _header-only-library: https://github.com/pypackaging-native/pkgconf-pypi/tree/main/examples/header-only-library
