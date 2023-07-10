"""
Admonition extension for Python-Markdown
========================================

Adds rST-style admonitions. Inspired by [rST][] feature with the same name.

[rST]: http://docutils.sourceforge.net/docs/ref/rst/directives.html#specific-admonitions  # noqa

See <https://Python-Markdown.github.io/extensions/admonition>
for documentation.

Original code Copyright [Tiago Serafim](https://www.tiagoserafim.com/).

Initial changes Copyright The Python Markdown Project

Further changes Copyright 2022-2023 Maarten Braakhekke, Peter Hill

License: [BSD](https://opensource.org/licenses/bsd-license.php)

"""

import re
import xml.etree.ElementTree as etree
from dataclasses import dataclass
from typing import ClassVar, List

from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

ADMONITION_TYPE = {
    "note": "info",
    "warning": "warning",
    "todo": "success",
    "bug": "danger",
    "history": "history",
}


class AdmonitionExtension(Extension):
    """Admonition extension for Python-Markdown."""

    def extendMarkdown(self, md):
        """Add Admonition to Markdown instance."""
        md.registerExtension(self)
        md.parser.blockprocessors.deregister("admonition", strict=False)
        md.preprocessors.register(AdmonitionPreprocessor(md), "admonition-pre", 105)
        md.parser.blockprocessors.register(
            AdmonitionProcessor(md.parser), "admonition", 105
        )


class AdmonitionProcessor(BlockProcessor):
    CLASSNAME = "alert"
    RE = re.compile(
        r"""(?:^|\n)!!! ?(?P<klass>[\w\-]+(?: +[\w\-]+)*)(?: +"(?P<title>.*?)")? *(?:\n|$)"""
    )
    RE_SPACES = re.compile("  +")

    def __init__(self, parser):
        """Initialization."""

        super().__init__(parser)

        self.current_sibling = None
        self.content_indent = 0

    def parse_content(self, parent, block):
        """Get sibling admonition.
        Retrieve the appropriate sibling element. This can get tricky when
        dealing with lists.
        """

        old_block = block
        the_rest = ""

        # We already acquired the block via test
        if self.current_sibling is not None:
            sibling = self.current_sibling
            block, the_rest = self.detab(block, self.content_indent)
            self.current_sibling = None
            self.content_indent = 0
            return sibling, block, the_rest

        sibling = self.lastChild(parent)

        if sibling is None or sibling.get("class", "").find(self.CLASSNAME) == -1:
            sibling = None
        else:
            # If the last child is a list and the content is sufficiently indented
            # to be under it, then the content's sibling is in the list.
            last_child = self.lastChild(sibling)
            indent = 0
            while last_child:
                if (
                    sibling
                    and block.startswith(" " * self.tab_length * 2)
                    and last_child
                    and last_child.tag in ("ul", "ol", "dl")
                ):
                    # The expectation is that we'll find an <li> or <dt>.
                    # We should get its last child as well.
                    sibling = self.lastChild(last_child)
                    last_child = self.lastChild(sibling) if sibling else None

                    # Context has been lost at this point, so we must adjust the
                    # text's indentation level so it will be evaluated correctly
                    # under the list.
                    block = block[self.tab_length :]
                    indent += self.tab_length
                else:
                    last_child = None

            if not block.startswith(" " * self.tab_length):
                sibling = None

            if sibling is not None:
                indent += self.tab_length
                block, the_rest = self.detab(old_block, indent)
                self.current_sibling = sibling
                self.content_indent = indent

        return sibling, block, the_rest

    def test(self, parent, block):
        if self.RE.search(block):
            return True
        return self.parse_content(parent, block)[0] is not None

    def run(self, parent, blocks):
        block = blocks.pop(0)

        if match := self.RE.search(block):
            if match.start() > 0:
                self.parser.parseBlocks(parent, [block[: match.start()]])
            block = block[match.end() :]  # removes the first line
            block, rest = self.detab(block)

            klass, title = self.get_class_and_title(match)
            div = etree.SubElement(parent, "div")
            div.set("class", f"alert alert-{ADMONITION_TYPE[klass]}")
            div.set("role", "alert")
            if title:
                header = etree.SubElement(div, "h4")
                header.text = title
                header.set("class", "alert-title")
        else:
            sibling, block, rest = self.parse_content(parent, block)
            # Sibling is a list item, but we need to wrap it's content should be wrapped in <p>
            if sibling.tag in ("li", "dd") and sibling.text:
                text = sibling.text
                sibling.text = ""
                p = etree.SubElement(sibling, "p")
                p.text = text

            div = sibling

        self.parser.parseChunk(div, block)

        if rest:
            # This block contained unindented line(s) after the first indented
            # line. Insert these lines as the first block of the master blocks
            # list for future processing.
            blocks.insert(0, rest)

    def get_class_and_title(self, match: re.Match):
        klass = self.RE_SPACES.sub(" ", match["klass"].lower())
        title = match["title"]
        if title is None:
            # no title was provided, use the capitalized classname as title
            # e.g.: `!!! note` will render
            # `<p class="admonition-title">Note</p>`
            title = klass.split(" ", 1)[0].capitalize()
        elif title == "":
            # an explicit blank title should not be rendered
            # e.g.: `!!! warning ""` will *not* render `p` with a title
            title = None
        return klass, title


class AdmonitionPreprocessor(Preprocessor):
    """Markdown preprocessor for dealing with FORD style admonitions.

    This preprocessor converts the FORD syntax for admonitions to
    the markdown admonition syntax.

    A FORD admonition starts with ``@<type>``, where ``<type>`` is one of:
    ``note``, ``warning``, ``todo``, ``bug``, or ``history``.
    An admonition ends at (in this order of preference):
        1. ``@end<type>``, where ``<type>`` must match the start marker
        2. an empty line
        3. a new note (``@<type>``)
        4. the end of the documentation lines

    The admonitions are converted to the markdown syntax, i.e. ``!!! Note``,
    followed by an indented block. Possible end markers are removed, as well
    as empty lines if they mark the end of an admonition.

    Todo:
        - Error handling
    """

    INDENT_SIZE: ClassVar[int] = 4
    INDENT: ClassVar[str] = " " * INDENT_SIZE
    ADMONITION_RE: ClassVar[re.Pattern] = re.compile(
        rf"""(?P<indent>\s*)
        @(?P<type>{"|".join(ADMONITION_TYPE.keys())})\s*
        (?P<posttxt>.*)
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    END_RE: ClassVar[re.Pattern] = re.compile(
        rf"""\s*@end(?P<type>{"|".join(ADMONITION_TYPE.keys())})
        \s*(?P<posttxt>.*)?""",
        re.IGNORECASE | re.VERBOSE,
    )
    admonitions: List["Admonition"] = []

    @dataclass
    class Admonition:
        """A single admonition block in the text.

        Attributes:
            type: admonition type (note, bug, etc.)
            start_idx: line index of start marker
            end_idx: end line index, one of: @end..., empty line,
                start marker of next  admonition, last line of text.
        """

        type: str
        start_idx: int
        end_idx: int = -1

    def run(self, lines: List[str]) -> List[str]:
        admonitions = self._find_admonitions(lines)
        return self._process_admonitions(admonitions, lines)

    def _find_admonitions(self, lines: List[str]) -> List[Admonition]:
        """Scans the lines to search for admonitions."""
        admonitions = []
        current_admonition = None

        for idx, line in enumerate(lines):
            if match := self.ADMONITION_RE.search(line):
                if current_admonition:
                    if current_admonition.end_idx == -1:
                        current_admonition.end_idx = idx
                    admonitions.append(current_admonition)
                current_admonition = self.Admonition(type=match["type"], start_idx=idx)

            if end := self.END_RE.search(line):
                if current_admonition:
                    if end["type"].lower() != current_admonition.type.lower():
                        # TODO: error: type of start and end marker dont' match
                        pass
                    current_admonition.end_idx = idx
                    admonitions.append(current_admonition)
                    current_admonition = None
                else:
                    # TODO: error: end marker found without start marker
                    pass

            elif line == "" and current_admonition and current_admonition.end_idx == -1:
                # empty line encountered while in an admonition. We set end_line but don't
                # move it to the list yet since an end marker (@end...) may follow
                # later.
                current_admonition.end_idx = idx

        if current_admonition:
            # We reached the last line and the last admonition wasn't moved to the list yet.
            if current_admonition.end_idx == -1:
                current_admonition.end_idx = idx
            admonitions.append(current_admonition)

        return admonitions

    def _process_admonitions(
        self, admonitions: List[Admonition], lines: List[str]
    ) -> List[str]:
        """Processes the admonitions to convert the lines to the markdown syntax."""

        # We handle the admonitions in the reverse order since
        # we may be deleting lines.
        for admonition in admonitions[::-1]:
            # last line--deal with possible text before or after end marker
            idx = admonition.end_idx
            if end := self.END_RE.search(lines[idx]):
                # Shove anything after the @end onto the next line
                if end["posttxt"]:
                    lines.insert(idx + 1, end["posttxt"])

                # Remove the @end and possibly the line too if it ends up blank
                lines[idx] = self.END_RE.sub("", lines[idx])
                if lines[idx].strip() == "":
                    del lines[idx]
                else:
                    # New ending is now next line
                    admonition.end_idx += 1

            # Indent any intermediate lines
            for idx in range(admonition.start_idx + 1, admonition.end_idx):
                if lines[idx] != "":
                    lines[idx] = self.INDENT + lines[idx]

            idx = admonition.start_idx
            if (match := self.ADMONITION_RE.search(lines[idx])) is None:
                # Somethine has gone seriously wrong
                raise RuntimeError(f"Missing start of @note: {lines[idx]}")

            lines[idx] = f"{match['indent']}!!! {admonition.type.capitalize()}"
            if posttxt := match["posttxt"]:
                lines.insert(idx + 1, self.INDENT + match["indent"] + posttxt)

        return lines
