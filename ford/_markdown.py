from markdown import Markdown, Extension
from markdown.inlinepatterns import InlineProcessor
from typing import Dict, List, Union, Optional
import re

from ford.md_environ import EnvironExtension
from ford.md_admonition import AdmonitionExtension
from ford._typing import PathLike


class MetaMarkdown(Markdown):
    """Helper subclass that captures our defaults"""

    def __init__(
        self,
        md_base: PathLike = ".",
        extensions: Optional[List[Union[str, Extension]]] = None,
        extension_configs: Optional[Dict[str, Dict]] = None,
        aliases: Optional[Dict[str, str]] = None,
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
