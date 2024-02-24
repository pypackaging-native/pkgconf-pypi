# SPDX-FileCopyrightText: 2024 The pypackaging-native developers
#
# SPDX-License-Identifier: MIT

project('pkgconf-pypi',
  version : '2.1.1',
  license : 'MIT AND ISC',
  license_files : ['LICENSE'],
  meson_version : '>=1.3.2',
)

# In pyproject.toml we only select the `runtime` tag to install,
# which contains the pkgconf executable and nothing else.
subproject('pkgconf',
  default_options : [
    'default_library=static',
    #'with-system-libdir=none',
  ],
)

