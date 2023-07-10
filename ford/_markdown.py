from markdown import Markdown, Extension
from typing import Any, Dict, List, Union, Optional

from ford.md_environ import EnvironExtension
from ford.md_extensions import AdmonitionExtension


class MetaMarkdown(Markdown):
    """Helper subclass that captures our defaults"""

    Meta: Dict[str, Any]

    def __init__(
        self,
        extensions: Optional[List[Union[str, Extension]]] = None,
        extension_configs: Optional[Dict[str, Dict]] = None,
    ):
        default_extensions: List[Union[str, Extension]] = [
            "markdown.extensions.meta",
            "markdown.extensions.codehilite",
            "markdown.extensions.extra",
            "mdx_math",
            EnvironExtension(),
            AdmonitionExtension(),
        ]
        if extensions is None:
            extensions = []

        super().__init__(
            extensions=default_extensions + extensions,
            output_format="html",
            extension_configs=extension_configs or {},
        )
