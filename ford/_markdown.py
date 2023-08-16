from __future__ import annotations

from markdown import Markdown, Extension
from markdown.inlinepatterns import InlineProcessor
from typing import Dict, List, Union, Optional, TYPE_CHECKING
import re
from xml.etree.ElementTree import Element

from ford.md_environ import EnvironExtension
from ford.md_admonition import AdmonitionExtension
from ford._typing import PathLike

if TYPE_CHECKING:
    from ford.fortran_project import Project


class MetaMarkdown(Markdown):
    """Helper subclass that captures our defaults"""

    def __init__(
        self,
        md_base: PathLike = ".",
        extensions: Optional[List[Union[str, Extension]]] = None,
        extension_configs: Optional[Dict[str, Dict]] = None,
        aliases: Optional[Dict[str, str]] = None,
        project=None,
    ):
        default_extensions: List[Union[str, Extension]] = [
            "markdown_include.include",
            "markdown.extensions.codehilite",
            "markdown.extensions.extra",
            "mdx_math",
            EnvironExtension(),
            AdmonitionExtension(),
        ]

        if aliases is not None:
            default_extensions.append(AliasExtension(aliases=aliases))

        if project is not None:
            default_extensions.append(FordLinkExtension(project=project))

        if extensions is None:
            extensions = []

        default_config = {"markdown_include.include": {"base_path": md_base}}
        default_config.update(extension_configs or {})

        super().__init__(
            extensions=default_extensions + extensions,
            output_format="html",
            extension_configs=default_config,
        )


ALIAS_RE = r"\|(.+?)\|"


class AliasProcessor(InlineProcessor):
    """Substitute text aliases of the form ``|foo|`` from a dictionary
    of aliases and their replacements"""

    def __init__(self, pattern: str, md: Markdown, aliases: Dict[str, str]):
        self.aliases = aliases
        super().__init__(pattern, md)

    def handleMatch(self, m: re.Match, data: str):  # type: ignore[override]
        try:
            sub = self.aliases[m.group(1)]
        except KeyError:
            return None, None, None

        return sub, m.start(0), m.end(0)


class AliasExtension(Extension):
    """Markdown extension to register `AliasProcessor`"""

    def __init__(self, **kwargs):
        self.config = {"aliases": [{}, "List of aliases"]}
        super().__init__(**kwargs)

    def extendMarkdown(self, md: Markdown):
        aliases = self.getConfig("aliases")
        md.inlinePatterns.register(
            AliasProcessor(ALIAS_RE, md, aliases=aliases), "ford_aliases", 175
        )


class FordLinkProcessor(InlineProcessor):
    """Replace links to different parts of the program, formatted as
    [[name]] or [[name(object-type)]] with the appropriate URL. Can
    also link to an item's entry in another's page with the syntax
    [[parent-name:name]]. The object type can be placed in parentheses
    for either or both of these parts.

    """

    LINK_RE = re.compile(
        r"""\[\[
        (?P<name>\w+(?:\.\w+)?)
        (?:\((?P<entity>\w+)\))?
        (?::(?P<child_name>\w+)
        (?:\((?P<child_entity>\w+)\))?)?
        \]\]""",
        re.VERBOSE | re.UNICODE,
    )

    def __init__(self, md: Markdown, project: Project):  # type: ignore[overrider]
        self.project = project
        self.md = md

    def getCompiledRegExp(self):
        return self.LINK_RE

    def convert_link(self, m: re.Match):
        item = self.project.find(**m.groupdict())

        # Could resolve full parent::child, so just try to find parent instead
        if m["child_name"] and item is None:
            parent_name = m["name"]
            print(
                f"Warning: Could not substitute link {m.group()}. "
                f'"{m["child_name"]}" not found in "{parent_name}", linking to page for "{parent_name}" instead'
            )
            item = self.project.find(m["name"], m["entity"])

        link = Element("a")

        # Nothing found, so give a blank link
        if item is None:
            name = m["name"]
            print(f"Warning: Could not substitute link {m.group()}. '{name}' not found")
            link.text = name
            return link

        link.attrib["href"] = item.get_url()
        link.text = item.name
        return link

    def handleMatch(self, m: re.Match, data: str):  # type: ignore[override]
        return self.convert_link(m), m.start(0), m.end(0)


class FordLinkExtension(Extension):
    """Markdown extension to register `FordLinkProcessor`"""

    def __init__(self, **kwargs):
        self.config = {"project": [kwargs.get("project", None), "Ford project"]}
        super().__init__(**kwargs)

    def extendMarkdown(self, md: Markdown):
        project = self.getConfig("project")
        md.inlinePatterns.register(
            FordLinkProcessor(md, project=project), "ford_links", 174
        )
