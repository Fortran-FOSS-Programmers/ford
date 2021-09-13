from ford.pagetree import PageNode, get_page_tree

from markdown import Markdown

from textwrap import dedent


def test_footnotes_on_one_page(tmp_path):
    """Check that footnotes only appear on the pages they are defined on,
    issue #327"""

    with open(tmp_path / "index.md", "w") as f:
        f.write("title: Index")

    with open(tmp_path / "a.md", "w") as f:
        f.write(
            dedent(
                """\
            title: Page A

            This has a footnote[^1] that should only appear on this page

            [^1]: This is the footnote on page A
            """
            )
        )

    with open(tmp_path / "b.md", "w") as f:
        f.write(
            dedent(
                """\
            title: Page B

            This page should not have any footnotes
            """
            )
        )

    md = Markdown(extensions=["markdown.extensions.meta", "markdown.extensions.extra"])
    result_dir = tmp_path / "result"
    nodes = get_page_tree(tmp_path, result_dir, md)

    assert len(nodes.subpages) == 2
    assert "This is the footnote on page A" in nodes.subpages[0].contents
    assert "This is the footnote on page A" not in nodes.subpages[1].contents


def test_footnotes_on_one_page_parse_failure(tmp_path):
    """Check that footnotes only appear on the pages they are defined on,
    even if we fail to parse one of the files, issue #327"""

    with open(tmp_path / "index.md", "w") as f:
        f.write("title: Index")

    with open(tmp_path / "a.md", "w") as f:
        f.write(
            dedent(
                """\
            This has a footnote[^1] that should only appear on this page

            [^1]: This is the footnote on page A
            """
            )
        )

    with open(tmp_path / "b.md", "w") as f:
        f.write(
            dedent(
                """\
            title: Page B

            This page should not have any footnotes
            """
            )
        )

    md = Markdown(extensions=["markdown.extensions.meta", "markdown.extensions.extra"])
    result_dir = tmp_path / "result"
    nodes = get_page_tree(tmp_path, result_dir, md)

    assert len(nodes.subpages) == 1
    assert "This is the footnote on page A" not in nodes.subpages[0].contents
