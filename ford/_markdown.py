from __future__ import annotations

from markdown import Markdown, Extension
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import Treeprocessor
from typing import Dict, List, Union, Optional, TYPE_CHECKING
import re
from xml.etree.ElementTree import Element
from contextlib import suppress
from pathlib import Path
from os.path import relpath

from ford.console import warn
from ford.md_environ import EnvironExtension
from ford.md_admonition import AdmonitionExtension
from ford._typing import PathLike

if TYPE_CHECKING:
    from ford.fortran_project import Project
    from ford.sourceform import FortranBase


class MetaMarkdown(Markdown):
    """Helper subclass that captures our defaults

    Parameters
    ----------
    md_base :
        Base path for md_include extension
    extensions :
        List of markdown extension names or instances
    extension_configs :
        Dictionary of markdown extension config settings
    aliases :
        Dictionary of text aliases
    project :
        Ford project instance
    relative :
        Should internal URLs be relative
    base_url :
        Base/project URL for relative links (required if
        ``relative`` is True)

    """

    def __init__(
        self,
        md_base: PathLike = ".",
        extensions: Optional[List[Union[str, Extension]]] = None,
        extension_configs: Optional[Dict[str, Dict]] = None,
        aliases: Optional[Dict[str, str]] = None,
        project: Optional[Project] = None,
        relative: bool = False,
        base_url: Optional[PathLike] = None,
    ):
        """make thing"""

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

        if relative:
            if base_url is None:
                raise ValueError("Expected path for base_url, got None")
            default_extensions.append(RelativeLinksExtension(base_url=base_url))

        if extensions is None:
            extensions = []

        default_config = {"markdown_include.include": {"base_path": md_base}}
        default_config.update(extension_configs or {})

        super().__init__(
            extensions=default_extensions + extensions,
            output_format="html",
            extension_configs=default_config,
        )

        self.current_context: Optional[FortranBase] = None
        self.current_path: Optional[Path] = None

    def reset(self):
        self.current_context = None
        self.current_path = None
        return super().reset()

    def convert(
        self,
        source: str,
        context: Optional[FortranBase] = None,
        path: Optional[Path] = None,
    ):
        """Convert from markdown to HTML

        Parameters
        ----------
        source : str
            Text to convert
        context : Optional[FortranBase]
            Current Ford object being processed
        path : Optional[Path]
            Current (output) path of page being processed

        """

        self.current_context = context
        self.current_path = path
        return super().convert(source)


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

    def __init__(self, md: MetaMarkdown, project: Project):  # type: ignore[overrider]
        self.project = project
        self.md: MetaMarkdown = md

    def getCompiledRegExp(self):
        return self.LINK_RE

    @property
    def warn_prefix(self) -> str:
        if context := self.md.current_context:
            return f"In '{context.filename}:{context.name}': "

        if self.md.current_path:
            return f"In file '{relpath(self.md.current_path)}': "

        return ""

    def convert_link(self, m: re.Match):
        item = None
        name = m["name"]

        def find_child(context):
            with suppress(ValueError):
                return context.find_child(name, m["entity"])

        if (context := self.md.current_context) is not None:
            item = find_child(context)

            if item is None and (parent := context.parent) is not None:
                item = find_child(parent)

            if m["child_name"] and item is not None:
                item = item.find_child(m["child_name"], m["child_entity"])

        if item is None:
            item = self.project.find(**m.groupdict())

        # Could resolve full parent::child, so just try to find parent instead
        if m["child_name"] and item is None:
            parent_name = name
            warn(
                f"{self.warn_prefix}Could not substitute link {m.group()}, "
                f'"{m["child_name"]}" not found in "{parent_name}", linking to page for "{parent_name}" instead'
            )
            item = self.project.find(name, m["entity"])

        link = Element("a")

        # Nothing found, so give a blank link
        if item is None:
            warn(
                f"{self.warn_prefix}Could not substitute link {m.group()}, '{name}' not found"
            )
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

    def extendMarkdown(self, md: MetaMarkdown):  # type: ignore[override]
        project = self.getConfig("project")
        md.inlinePatterns.register(
            FordLinkProcessor(md, project=project), "ford_links", 174
        )


class RelativeLinksTreeProcessor(Treeprocessor):
    """Modify link URLs to be relative to the given base URL"""

    md: MetaMarkdown

    def __init__(self, md: MetaMarkdown, base_url: Path):
        self.base_url = base_url.resolve()
        super().__init__(md)

    def _fix_attrib(self, tag: Element, attrib: str):
        if attrib not in tag.attrib:
            return

        tag_path = Path(tag.attrib[attrib]).resolve()
        # FIXME: In py3.9, this can be Path.is_relative_to
        if self.base_url in tag_path.parents:
            tag.attrib[attrib] = relpath(tag_path, self.md.current_path)

    def run(self, root: Element):
        if self.md.current_path is None:
            return

        for link in root.iter("a"):
            self._fix_attrib(link, "href")

        for link in root.iter("img"):
            self._fix_attrib(link, "src")


class RelativeLinksExtension(Extension):
    """Markdown extension to register `RelativeLinksTreeProcessor`"""

    def __init__(self, **kwargs):
        self.config = {"base_url": [kwargs["base_url"], "Base URL of project"]}
        super().__init__(**kwargs)

    def extendMarkdown(self, md: MetaMarkdown):  # type: ignore[override]
        base_url: Path = self.getConfig("base_url")
        md.treeprocessors.register(
            RelativeLinksTreeProcessor(md, base_url=base_url), "relative_links", 5
        )
