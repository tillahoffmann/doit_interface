import doctest


master_doc = "README"
extensions = [
    "sphinx.ext.doctest",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
]
project = "doit_interface"
napoleon_custom_sections = [("Returns", "params_style")]
plot_formats = [
    ("png", 144),
]
html_theme = "nature"

doctest_global_setup = """
from doit_interface import *
manager = Manager.get_instance()
"""
doctest_global_cleanup = """
manager.clear()
"""
doctest_default_flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

# Configure autodoc to avoid excessively long fully-qualified names.
add_module_names = False
autodoc_typehints_format = "short"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
    "torch": ("https://pytorch.org/docs/stable/", None),
}
