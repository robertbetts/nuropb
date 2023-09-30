# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import datetime
from pathlib import Path

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
sys.path.insert(0, os.path.abspath("../../examples"))
sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

year = datetime.datetime.now().year
project = 'nuropb'
author = 'Robert Betts'
copyright = f'{year}, {author}'
release = '0.1.6'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "autodoc2",
    "sphinx_rtd_theme",
    # "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    # "sphinxext.opengraph",
    # "sphinxcontrib.spelling",
    # "sphinx_copybutton",
    # "autoapi.extension",
    # "nbsphinx",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


ogp_site_url = "https://nuropb.readthedocs.io/en/latest/"

spelling_warning = True
spelling_show_suggestions = True

myst_enable_extensions = ["fieldlist"]
autodoc2_packages = [
    {
        "path": "../../examples/",
        "auto_mode": True,
    },
    {
        "path": "../../src/nuropb",
        "auto_mode": True,
    },
]
autodoc2_render_plugin = "myst"

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
