from ford.pagetree import get_page_tree
from ford._markdown import MetaMarkdown

from textwrap import dedent
from locale import getpreferredencoding


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

    md = MetaMarkdown()
    result_dir = tmp_path / "result"
    nodes = get_page_tree(tmp_path, result_dir, tmp_path / "doc", md)

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
            This page is missing a title and so expected not to be parsed

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

    md = MetaMarkdown()
    result_dir = tmp_path / "result"
    nodes = get_page_tree(tmp_path, result_dir, tmp_path / "doc", md)

    assert len(nodes.subpages) == 1
    assert "This is the footnote on page A" not in nodes.subpages[0].contents


def test_non_utf8_encoding(tmp_path):
    """This is not really a full test for issue #518, as it only tests
    the lower part of the call-tree. A more thorough test would do
    something like encode a whole project in the non-default encoding.

    """
    # Try to get an encoding which is *not* the default for `open`
    encoding = "gbk" if getpreferredencoding().lower() == "utf-8" else "utf-8"

    with open(tmp_path / "index.md", "wb") as f:
        f.write(
            dedent(
                """\
        ---
        title: Specification
        ---

        @warning
        本文档是一个简易的规范文档，仅供参考
        """
            ).encode(encoding)
        )

    md = MetaMarkdown()
    result_dir = tmp_path / "result"
    nodes = get_page_tree(tmp_path, result_dir, tmp_path / "doc", md, encoding=encoding)

    assert "本文档是" in nodes.contents
