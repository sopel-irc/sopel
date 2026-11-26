"""Sopel Sphinx extension.

.. warning::

    This is a work in progress and may change between patch version without
    warning. DO NOT USE unless you like broken proof of concept.
"""
from __future__ import annotations

from importlib import import_module
import inspect
from typing import TYPE_CHECKING

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.domains import Domain
from sphinx.pycode import ModuleAnalyzer
from sphinx.util.docutils import SphinxDirective
from sphinx.util.parsing import nested_parse_to_nodes

from sopel.config.types import BaseValidated, StaticSection


if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata


STATIC_DOCSTRING = inspect.getdoc(StaticSection)
"""The docstring of the base class for plugin configuration section."""


class SopelConfigDirective(SphinxDirective):
    """A directive to display a Sopel Plugin config documentation.

    Usage::

        .. sopel:config:: section_name
            :class: yourplugin.path.to.YourPluginConfigSection

    This will display a section with:

    * the section's name as title
    * the class's docstring as description (optional)
    * a definition list composed of the class's attributes documentation
    * the directive's content (optional)

    """
    required_arguments = 1
    has_content = True
    option_spec = {
        'class': directives.unchanged_required,
    }

    def run(self) -> list[nodes.Node]:
        """Make a definition list for a Plugin's config section class.

        .. ::

            <definition_list>
                <definition_list_item>
                    <term>
                        Term
                    <definition>
                        <paragraph>
                            Definition.
        """
        section_name = self.arguments[0]
        class_dotted_path = self.options['class']

        module_path, _, class_name = class_dotted_path.rpartition('.')
        module = import_module(module_path)
        config_class = getattr(module, class_name, None)

        if config_class is None:
            raise RuntimeError('Cannot find class...')
        elif not issubclass(config_class, StaticSection):
            raise RuntimeError('Class is not a static section...')

        # heading section
        head_nodes: list[nodes.Node] = [
            nodes.paragraph(text=f'Section [{section_name}]'),
        ]

        # get config class's docstring
        docstring = inspect.getdoc(config_class)
        if docstring and docstring != STATIC_DOCSTRING:
            # add docstring if and only if it's not the base class's docstring
            head_nodes.extend(self.parse_text_to_nodes(docstring))

        # definition list
        def_nodes: list[nodes.Node] = []
        analyzer = ModuleAnalyzer.for_string(
            inspect.getsource(config_class),
            module_path,
        )
        analyzer.analyze()

        for name, value in inspect.getmembers(config_class):
            if isinstance(value, BaseValidated):
                def_nodes.append(
                    nodes.definition_list_item('', *[
                        nodes.term('', name)
                    ])
                )

                attribute_lines = analyzer.attr_docs.get((class_name, name), [])
                if attribute_lines:
                    attribute_nodes = nested_parse_to_nodes(
                        state=self.state,
                        text='\n'.join(attribute_lines),
                        offset=0,
                    )
                    def_nodes.append(
                        nodes.definition('', *attribute_nodes)
                    )

        def_nodes = [nodes.definition_list('', *def_nodes)]

        # post-content section
        desc_nodes = self.parse_content_to_nodes()

        return head_nodes + def_nodes + desc_nodes


class SopelDomain(Domain):
    name = 'sopel'
    label = 'Sopel Sphinx Extension'
    directives = {
        'config': SopelConfigDirective,
    }
    data_version = 0

    def get_full_qualified_name(self, node):
        return f'sopel.{node.arguments[0]}'


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_domain(SopelDomain)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
