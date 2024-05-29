import pkgconf


project = 'pkgconf-pypi'
copyright = '2024, The pkgconf and pypackaging-native contributors'
author = 'Filipe Laíns, Ralf Gommers'

version = release = pkgconf.__version__

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx_design',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
}

html_theme = 'furo'
html_title = f'{project} {version}'
