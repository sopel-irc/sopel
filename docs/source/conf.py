from __future__ import generator_stop
# Sopel IRC Bot documentation build configuration file, created by
# sphinx-quickstart on Mon Jul 16 23:45:29 2012.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import subprocess
from datetime import date

from packaging.version import Version

from sopel import __version__

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#sys.path.insert(0, os.path.abspath('.'))

# -- General configuration -----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = '7.1'  # todo: upgrade when Py3.8 reaches EOL

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.intersphinx',
    'sphinxcontrib.autoprogram',
    'sphinx_rfcsection',
]
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sqlalchemy': ('https://docs.sqlalchemy.org/en/14/', None),
}

# Make Sphinx warn for references (methods, functions, etc.) it can't find
nitpicky = True
# Except for certain not-actually-reference things that aren't published in the
# docs or don't actually exist except as shorthand for the reader
nitpick_ignore = [
    ('py:class', 'callable'),
    ('py:class', 'depends on subclass'),
    ('py:class', 'mixed'),
    ('py:class', 'sopel.tools.jobs.Job'),
    ('py:class', 'sopel.tools.jobs.JobScheduler'),
    ('py:exc', 'plugins.exceptions.PluginNotRegistered'),
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'Sopel'
copyright = '2012-{}, Sopel contributors'.format(date.today().year)

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = __version__
# The full version, including alpha/beta/rc tags.
release = __version__

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# The reST default role (used for this markup: `text`) to use for all documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'friendly'
pygments_dark_style = 'monokai'

# A list of ignored prefixes for module index sorting.
modindex_common_prefix = ['sopel.']

# If a signature’s length in characters exceeds the number set, each parameter
# within the signature will be displayed on an individual logical line.
maximum_signature_line_length = 80


# -- Options for autodoc -------------------------------------------------------

autodoc_type_aliases = {
    'Casemapping': 'sopel.tools.identifiers.Casemapping',
    'IdentifierFactory': 'sopel.tools.identifiers.IdentifierFactory',
    'ModeTuple': 'sopel.irc.modes.ModeTuple',
    'ModeDetails': 'sopel.irc.modes.ModeDetails',
    'PrivilegeDetails': 'sopel.irc.modes.PrivilegeDetails',
}


# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'furo'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    'navigation_with_keys': True,
    'light_logo': 'sopel-black.png',
    'dark_logo': 'sopel-white.png',
    'light_css_variables': {
        'sidebar-tree-space-above': '1em',
    }
}

# Extra CSS files to include, relative to html_static_path.
html_css_files = [
    'custom.css',
]

# Extra JavaScript files to include, relative to html_static_path.
#html_js_files = []

# Add any paths that contain custom themes here, relative to this directory.
#html_theme_path = []

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = '_static/favicon.ico'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_domain_indices = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
#html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
#html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = 'sopel'


# -- Options for LaTeX output --------------------------------------------------

latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
#'papersize': 'letterpaper',

# The font size ('10pt', '11pt' or '12pt').
#'pointsize': '10pt',

# Additional stuff for the LaTeX preamble.
#'preamble': '',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'sopel.tex', 'Sopel IRC Bot Documentation',
   'Sopel contributors', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# If true, show page references after internal links.
#latex_show_pagerefs = False

# If true, show URL addresses after external links.
#latex_show_urls = False

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_domain_indices = True


# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
# Note from `man 7 man-pages`
# 1: User commands (Programs)
# 2: System calls
# 3: Library calls
# 4: Special files (devices)
# 5: File formats and configuration files
# 6: Games
# 7: Overview, conventions, and miscellaneous
# 8: System management commands
man_pages = [
    ('cli', 'sopel', 'Sopel IRC Bot Command Line',
     ['Sopel contributors'], 1),
    ('package', 'sopel', 'Sopel IRC Bot Documentation',
     ['Sopel contributors'], 3),
    ('configuration', 'sopel', 'Sopel IRC Bot Configuration',
     ['Sopel contributors'], 5),
]

# If true, show URL addresses after external links.
#man_show_urls = False


# -- Options for Texinfo output ------------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
  ('index', 'sopel', 'Sopel IRC Bot Documentation',
   'Sopel contributors', 'SopelIRCBot', 'Simple, extendible IRC bot.',
   'Miscellaneous'),
]

# Documents to append as an appendix to all manuals.
#texinfo_appendices = []

# If false, no module index is generated.
#texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
#texinfo_show_urls = 'footnote'


try:
    if Version(__version__).is_prerelease:
        tags.add("preview")

    is_dirty = bool(subprocess.check_output(["git", "status", "--untracked-files=no", "--porcelain"], text=True).strip())
    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    github_ref = "https://github.com/sopel-irc/sopel/commit/{commit_hash}".format(commit_hash=commit_hash)
    build_info = "(built against `{commit_hash} <{github_ref}>`_)".format(commit_hash=commit_hash[:7], github_ref=github_ref)
except Exception as exc:
    build_info = "(built against an unknown commit)"


rst_prolog = """
.. only:: preview

    .. warning:: This is preview documentation for Sopel |version| {build_info}.

                 Click `here <https://sopel.chat/docs/>`_ for the latest stable documentation.

""".format(build_info=build_info)
