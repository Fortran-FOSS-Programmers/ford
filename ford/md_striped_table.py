from markdown import Markdown, Extension
from markdown.treeprocessors import Treeprocessor


def makeExtension(**kwargs):
    return StripedTableCSSExtension(**kwargs)


class StripedTableCSSExtension(Extension):
    """Add CSS class to alternate rows in table"""

    def extendMarkdown(self, md: Markdown, *args, **kwargs):
        md.treeprocessors.register(StripedTableCSSTreeprocessor(md), "table_css", 100)
        md.registerExtension(self)


class StripedTableCSSTreeprocessor(Treeprocessor):
    def run(self, root):
        for element in root.iter():
            if element.tag == "table":
                element.set("class", "table table-striped")
