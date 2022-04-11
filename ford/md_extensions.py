"""
Admonition extension for Python-Markdown
========================================

Adds rST-style admonitions. Inspired by [rST][] feature with the same name.

[rST]: http://docutils.sourceforge.net/docs/ref/rst/directives.html#specific-admonitions  # noqa

See <https://Python-Markdown.github.io/extensions/admonition>
for documentation.

Original code Copyright [Tiago Serafim](https://www.tiagoserafim.com/).

All changes Copyright The Python Markdown Project

License: [BSD](https://opensource.org/licenses/bsd-license.php)

"""

from markdown.extensions import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.preprocessors import Preprocessor
import xml.etree.ElementTree as etree
import re
from dataclasses import dataclass
from typing import List, Optional, ClassVar

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
        md.preprocessors.register(AdmonitionPreprocessor(md), "admonition-pre", 105)
        md.parser.blockprocessors.register(
            AdmonitionProcessor(md.parser), "admonition", 105
        )


class AdmonitionProcessor(BlockProcessor):

    CLASSNAME = "alert"
    RE = re.compile(r'(?:^|\n)!!! ?([\w\-]+(?: +[\w\-]+)*)(?: +"(.*?)")? *(?:\n|$)')
    RE_SPACES = re.compile("  +")

    def __init__(self, parser):
        """Initialization."""

        super().__init__(parser)

        self.current_sibling = None
        self.content_indention = 0

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
        else:
            return self.parse_content(parent, block)[0] is not None

    def run(self, parent, blocks):
        block = blocks.pop(0)
        m = self.RE.search(block)

        if m:
            if m.start() > 0:
                self.parser.parseBlocks(parent, [block[: m.start()]])
            block = block[m.end() :]  # removes the first line
            block, theRest = self.detab(block)
        else:
            sibling, block, theRest = self.parse_content(parent, block)

        if m:
            klass, title = self.get_class_and_title(m)
            div = etree.SubElement(parent, "div")
            div.set("class", "alert alert-{}".format(ADMONITION_TYPE[klass]))
            div.set("role", "{}".format("alert"))
            header = etree.SubElement(div, "h4")
            header.text = klass.capitalize()
        else:
            # Sibling is a list item, but we need to wrap it's content should be wrapped in <p>
            if sibling.tag in ("li", "dd") and sibling.text:
                text = sibling.text
                sibling.text = ""
                p = etree.SubElement(sibling, "p")
                p.text = text

            div = sibling

        self.parser.parseChunk(div, block)

        if theRest:
            # This block contained unindented line(s) after the first indented
            # line. Insert these lines as the first block of the master blocks
            # list for future processing.
            blocks.insert(0, theRest)

    def get_class_and_title(self, match):
        klass, title = match.group(1).lower(), match.group(2)
        klass = self.RE_SPACES.sub(" ", klass)
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

    This preprocessor converts the FORD syntax for admonitions (`@note`,
    `@bug`, etc.) to the markdown admonition syntax (`!!! Note`)

    A FORD admonition starts with `@<type>`, where `<type>` is one of:
    `note`, `warning`, `todo`, `bug`, or `history`.
    An admonition ends at (in this order of preference):
        1. `@end<type>`, where <type>` must match the start marker
        2. an empty line
        3. a new note (`@<type>`)
        4. the end of the documentation lines

    The admonitions are converted to the markdown syntax, i.e. `!!! Note`,
    followed by an indented block. Possible end markers are removed, as well
    as empty lines if they mark the end of an admonition.

    Todo:
        - Error handling
        - Support for end marker embedded in line.

    """

    INDENT_SIZE: ClassVar[int] = 4
    ADMONITION_RE: ClassVar[re.Pattern] = re.compile(
        r"@(?P<end>end)?(?P<type>{})\s*(?P<txt>.*)".format(
            "|".join(ADMONITION_TYPE.keys())
        ),
        re.IGNORECASE,
    )
    admonitions: List["Admonition"] = []

    @dataclass
    class Admonition:
        type: str
        start_idx: int
        end_idx: Optional[int] = None
        start_line_txt: Optional[str] = None

    def run(self, lines: List[str]) -> List[str]:
        self.lines = lines
        self._find_admonitions()
        self._process_admonitions()
        return self.lines

    def _process_admonitions(self):
        """Processes the admonitions."""

        # We handle the admonitions in the reverse order since
        # we may be deleting lines.
        for admonition in self.admonitions[::-1]:
            for idx in range(admonition.start_idx + 1, admonition.end_idx + 1):
                if idx == admonition.end_idx:
                    if self.lines[idx] == "" or "@end" in self.lines[idx].lower():
                        del self.lines[admonition.end_idx]
                        continue
                    elif self.lines[idx].startswith("!!!"):
                        continue
                if self.lines[idx] != "":
                    self.lines[idx] = " " * self.INDENT_SIZE + self.lines[idx]

            self.lines[admonition.start_idx] = "!!! " + admonition.type.capitalize()
            if admonition.start_line_txt:
                self.lines.insert(
                    admonition.start_idx + 1,
                    " " * self.INDENT_SIZE + admonition.start_line_txt,
                )

    def _find_admonitions(self):
        """Scans the lines to search for admonitions."""
        self.admonitions = []
        current_admonition = None

        for idx, line in enumerate(self.lines):
            match = self.ADMONITION_RE.search(line)

            if match and not match.group("end"):
                if current_admonition:
                    if not current_admonition.end_idx:
                        current_admonition.end_idx = idx
                    self.admonitions.append(current_admonition)
                current_admonition = self.Admonition(
                    type=match.group("type"),
                    start_idx=idx,
                    start_line_txt=match.group("txt"),
                )

            elif match and match.group("end"):
                if current_admonition:
                    if match.group("type").lower() != current_admonition.type.lower():
                        pass  # error: type of start and end marker dont' match
                    current_admonition.end_idx = idx
                    self.admonitions.append(current_admonition)
                    current_admonition = None
                else:
                    pass  # error: end marker found without start marker

            elif line == "" and current_admonition and not current_admonition.end_idx:
                # white line encountered while in an admonition. We set end_line but don't
                # move it to the list yet since an end marker (@end...) may follow
                # later.
                current_admonition.end_idx = idx

        if current_admonition:
            # We reached the last line and the last admonition wasn't moved to the list yet.
            if not current_admonition.end_idx:
                current_admonition.end_idx = idx
            self.admonitions.append(current_admonition)
