from markdown import Markdown, Extension
from typing import Dict, List, Union, Optional

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
    ):
        default_extensions: List[Union[str, Extension]] = [
            "markdown_include.include",
            "markdown.extensions.codehilite",
            "markdown.extensions.extra",
            "mdx_math",
            EnvironExtension(),
            AdmonitionExtension(),
        ]
        if extensions is None:
            extensions = []

        default_config = {"markdown_include.include": {"base_path": md_base}}
        default_config.update(extension_configs or {})

        super().__init__(
            extensions=default_extensions + extensions,
            output_format="html",
            extension_configs=default_config,
        )
