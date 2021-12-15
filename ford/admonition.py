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


NOTE_TYPE = {
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
    RE = re.compile(rf'(?:^|\n)@({"|".join(NOTE_TYPE.keys())})(?: +(.*?))? *(?:\n|$)')

    def __init__(self, parser):
        """Initialization."""

        super().__init__(parser)

        self.current_sibling = None
        self.content_indention = 0

    def parse_content(self, parent, block):
        """Get sibling admontion.

        Retrieve the appropriate sibling element. This can get tricky
        when dealing with lists.

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
            # If the last child is a list and the content is idented sufficient
            # to be under it, then the content's is sibling is in the list.
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
                    # We should get it's last child as well.
                    sibling = self.lastChild(last_child)
                    last_child = self.lastChild(sibling) if sibling else None

                    # Context has been lost at this point, so we must adjust the
                    # text's identation level so it will be evaluated correctly
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
            div.set("class", "{} {}".format(self.CLASSNAME, klass))
            if title:
                p = etree.SubElement(div, "h4")
                p.text = title
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
        title = match.group(1).lower()
        klass = f"alert-{NOTE_TYPE[title]}"
        return klass, title.capitalize()


class AdmonitionPreprocessor(Preprocessor):
    NOTE_RE = re.compile(rf"@{'|'.join(NOTE_TYPE.keys())}")

    def run(self, lines):
        new_lines = []
        needs_indent = False
        for line in lines:
            if line.strip() == "":
                needs_indent = False
            match = self.NOTE_RE.search(line)
            if match:
                if match.end(0) == len(line):
                    new_lines.append(line)
                    continue
                new_lines.append(line[: match.start(0) - 1])
                new_lines.append("")
                new_lines.append(line[match.start(0) - 1 : match.end(0)])
                new_lines.append(f"    {line[match.end(0):]}")
                new_lines.append("")
                needs_indent = True
            elif needs_indent:
                new_lines.append(f"    {line}")
            else:
                new_lines.append(line)

        return new_lines
