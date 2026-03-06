# SPDX-License-Identifier: Apache-2.0
# Configuration file for the Sphinx documentation builder.

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version

# -- Project information

project = "Chiltepin"
copyright = "2024-2026, The Regents of the University of Colorado and contributors"
author = "Christopher W Harrop"

# Get version from the installed package
try:
    release = get_version("chiltepin")
    version = release
except PackageNotFoundError:
    # Package not installed - use a placeholder for local development
    release = "dev"
    version = "dev"

# -- General configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

# -- Options for HTML output

html_theme = "sphinx_rtd_theme"

# -- Options for EPUB output
epub_show_urls = "footnote"
