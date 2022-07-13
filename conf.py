import doctest


master_doc = "README"
extensions = [
    "sphinx.ext.doctest",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_rtd_theme",
]
project = "🎯 doit interface"
napoleon_custom_sections = [("Returns", "params_style")]
plot_formats = [
    ("png", 144),
]
html_theme = "sphinx_rtd_theme"

doctest_global_setup = """
from doit_interface import *
manager = Manager()
manager.__enter__()
"""
doctest_global_cleanup = """
manager.__exit__()
"""
doctest_default_flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

# Configure autodoc to avoid excessively long fully-qualified names.
add_module_names = False
autodoc_typehints_format = "short"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "doit": ("https://pydoit.org", None),
}
