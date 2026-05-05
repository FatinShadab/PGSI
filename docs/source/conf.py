import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath("../../src"))

project = "PGSI Analyzer"
author = "PGSI Contributors"
copyright = f"{datetime.now().year}, {author}"
release = "1.0.0"
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

autosummary_generate = True
autodoc_member_order = "bysource"

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
