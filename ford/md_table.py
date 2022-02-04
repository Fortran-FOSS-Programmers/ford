from markdown import Markdown, Extension
from markdown.treeprocessors import Treeprocessor
from itertools import cycle


def makeExtension(**kwargs):
    return ZebraTableCSSExtension(**kwargs)


class ZebraTableCSSExtension(Extension):
    """Add CSS class to alternate rows in table"""

    def extendMarkdown(self, md: Markdown, *args, **kwargs):
        md.treeprocessors.register(ZebraTableCSSTreeprocessor(md), "table_css", 100)
        md.registerExtension(self)


class ZebraTableCSSTreeprocessor(Treeprocessor):
    def run(self, root):
        for element in root.iter():
            if element.tag == "table":
                element.set("class", "table")

                rows = element.find("tbody").findall("tr")
                zebra_cycler = cycle(["active", ""])

                for row, style in zip(rows, zebra_cycler):
                    row.set("class", style)
