# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
from importlib.metadata import version as _version

sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "xNFT - Near-Field Antenna Measurement System"
copyright = "2025-%Y, LEmmA Group, Michigan State University"
author = "LEmmA Group, Michigan State University"

release = _version("xnft")
version = release

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "numpydoc",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "sphinx.ext.imgmath",
    "sphinx_copybutton",
]

autodoc_typehints = "description"
autosummary_generate = True
numpydoc_xref_param_type = False
numpydoc_show_class_members = False
numpydoc_xref_ignore = {"optional", "type_without_description", "BadException"}
# Run docstring validation as part of build process
numpydoc_validation_checks = {"all", "GL01", "SA04", "RT03"}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# -- Sphinx Version Configuration -----------------------------------------
smv_branch_whitelist = r"^.*$"  # Include all branches

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]

html_theme_options = {
    "gitlab_url": "https://gitlab.msu.edu/ece-lemma/xnft",
    "show_prev_next": False,
    "logo": {
      "image_light": "xnft.svg",
      "image_dark": "xnft.svg",
    },
}

html_title = f"{project} v{version} Manual"
html_last_updated_fmt = "%b %d, %Y"

# Output file base name for HTML help builder.
htmlhelp_basename = "project-templatedoc"

# --- LaTeX PDF Output Configuration ---
latex_engine = "xelatex"
latex_documents = [('index', 'xnft-docs.tex', project, author, 'manual')]
