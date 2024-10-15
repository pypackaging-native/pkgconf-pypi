************
pkgconf-pypi
************

The `pkgconf PyPI package`_ provides a pre-built pkgconf_ binary, as well an
integration layer for Python packages.

Using the integration layer, Python packages can register their own
``pkgconf`` paths, which will be searched by the ``pkgconf`` and ``pkg-config``
scripts shipped by this package.


Registering ``pkg-config`` paths
================================

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
===================

When you run the ``pkgconf`` executable embedded in this package, the ``PKG_CONFIG_PATH``
environment variable will be set so that ``pkgconf`` can find the .pc files registered
by the ``pkg-config`` entrypoint_. If the ``PKG_CONFIG_PATH`` environment variable is
already set, it will be appended to.

If the embedded pkgconf cannot find a package, by default it will fallback to the system
``pkgconf``/``pkg-config``, which may find packages present on the system. To disable
this behavior, set the ``PKGCONF_PYPI_EMBEDDED_ONLY=1`` environment variable.

API
===

.. automodule:: pkgconf
   :members:
   :undoc-members:
   :show-inheritance:


.. _pkgconf PyPI package: https://pypi.org/project/pkgconf/
.. _pkgconf: https://github.com/pkgconf/pkgconf
.. _entrypoint: https://packaging.python.org/en/latest/specifications/entry-points
.. _header-only-library: https://github.com/pypackaging-native/pkgconf-pypi/tree/main/examples/header-only-library
