# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import subprocess
import sys
import os

subprocess.call(
    [
        "make",
        "systemconfigs",
    ]
)

subprocess.call(
    [
        "make",
        "tags",
    ]
)

project = "Benchpark"
copyright = "2023, LLNS LLC"
author = "Olga Pearce, Alec Scott, Peter Scheibel, Greg Becker, Riyaz Haque, and Nathan Hanford"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_rtd_theme",
    "sphinxcontrib.programoutput",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

sys.path.insert(0, os.path.abspath("../lib"))

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", ".spack-env"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_static_path = ["_static"]
html_js_files = [
    "https://cdn.datatables.net/1.10.23/js/jquery.dataTables.min.js",
    "main.js",
]
html_css_files = [
    (
        "https://cdn.datatables.net/1.10.23/css/jquery.dataTables.min.css",
        {"priority": 800},
    ),
    ("css/custom.css", {"priority": 999}),
]
html_logo = "_static/images/benchpark-dark.svg"
html_theme = "sphinx_rtd_theme"
html_theme_options = {"logo_only": True}
