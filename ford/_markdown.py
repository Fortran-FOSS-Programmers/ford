from __future__ import annotations

from markdown import Markdown, Extension
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import Treeprocessor
from markdown.preprocessors import Preprocessor
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
    base_url :
        Base/project URL for relative links (required if
        ``relative`` is True)

    """

    def __init__(
        self,
        md_base: PathLike = ".",
        base_url: PathLike = ".",
        extensions: Optional[List[Union[str, Extension]]] = None,
        extension_configs: Optional[Dict[str, Dict]] = None,
        aliases: Optional[Dict[str, str]] = None,
        project: Optional[Project] = None,
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

        self.base_url = Path(base_url)
        if base_url != ".":
            default_extensions.append(RelativeLinksExtension())

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
        source:
            Text to convert
        context:
            Current Ford object being processed
        path:
            Current (output) path of page being processed

        """

        self.current_context = context
        if (
            path is None
            and context is not None
            and (url := context.get_url()) is not None
        ):
            # This is a bit of a pain, but when making `[[ford]]` links, we want
            # the link to be relative to the page the link is from. However, we
            # use the entity description both on the entity page, and the list
            # pages, so the same relative url needs to work from both. Luckily
            # we know the directory layout, so just make a relative link from a
            # (non-existent) sibling directory
            self.current_path = (
                self.base_url / Path(url).parent.parent / "non-existent dir"
            )
        else:
            self.current_path = path
        return super().convert(source)


class AliasPreprocessor(Preprocessor):
    r"""Substitute text aliases of the form ``|foo|`` from a dictionary
    of aliases and their replacements.
    The backslash ``\`` acts as an escape character, aliases of the
    form ``\|foo|`` will not be replaced, but instead copied verbatim
    without the preceding backslash.
    """

    # pattern to match alias only if not preceded by `\`
    ALIAS_RE = re.compile(r"(?<!\\)\|([^ ].*?[^ ]?)\|")

    def __init__(self, md: Markdown, aliases: Dict[str, str]):
        self.aliases = aliases

        super().__init__(md)

    def _lookup(self, m: re.Match):
        """Return alias replacement for match. If not found, return
        the original text, including pipes

        """
        return self.aliases.get(m.group(1), f"|{m.group(1)}|")

    def run(self, lines: List[str]) -> List[str]:
        for line_num, line in enumerate(lines):
            # replace the real aliases
            line = self.ALIAS_RE.sub(self._lookup, line)
            # replace the escaped aliases verbatim, without the preceding `\`
            line = re.sub(r"\\(\|([^ ].*?[^ ]?)\|)", r"\g<1>", line)
            lines[line_num] = line
        return lines


class AliasExtension(Extension):
    """Markdown extension to register `AliasPreprocessor`"""

    def __init__(self, **kwargs):
        self.config = {"aliases": [{}, "List of aliases"]}
        super().__init__(**kwargs)

    def extendMarkdown(self, md: Markdown):
        aliases = self.getConfig("aliases")
        # Needs to happen before tables to avoid clashes, see
        # https://github.com/Fortran-FOSS-Programmers/ford/issues/604
        md.preprocessors.register(
            AliasPreprocessor(md, aliases=aliases), "ford_aliases", 50
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
            # This is allowed to fail because we might be looking for
            # "entity" in the wrong context
            with suppress(ValueError):
                return context.find_child(name, m["entity"])

        if (context := self.md.current_context) is not None:
            item = find_child(context)

            if item is None and (parent := context.parent) is not None:
                item = find_child(parent)

            if m["child_name"] and item is not None:
                try:
                    # This isn't allowed to fail because the user has
                    # given us all the information required
                    item = item.find_child(m["child_name"], m["child_entity"])
                except ValueError as e:
                    raise ValueError(f"Error when parsing link '{m.group()}': {e}")

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

        if (item_url := item.get_url()) is None:
            # This is really to keep mypy happy
            raise RuntimeError(f"Found item {name} but no url")

        # Make sure links are relative to base url, unless they are
        # already absolute (because they're external)
        if item_url.startswith("http"):
            rel_url = item_url
        else:
            full_url = self.md.base_url / item_url
            rel_url = relpath(full_url, self.md.current_path)
        link.attrib["href"] = str(rel_url)
        link.text = item.name
        return link

    def handleMatch(self, m: re.Match, data: str):  # type: ignore[override]
        """Return the converted match, along with start and end positions"""
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

    def __init__(self, md: MetaMarkdown):
        self.base_url = md.base_url.resolve()
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
        super().__init__(**kwargs)

    def extendMarkdown(self, md: MetaMarkdown):  # type: ignore[override]
        md.treeprocessors.register(RelativeLinksTreeProcessor(md), "relative_links", 5)
