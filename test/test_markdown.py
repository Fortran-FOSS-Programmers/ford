from ford._markdown import MetaMarkdown

from textwrap import dedent


def test_sub_alias():
    result = MetaMarkdown(aliases={"a": "b"}).convert("|a|")
    assert result == "<p>b</p>"

    result = MetaMarkdown(aliases={"a": "b"}).convert("|undefined|")
    assert result == "<p>|undefined|</p>"


def test_sub_alias_escape():
    def_alias = {"a": "b"}

    result = MetaMarkdown(aliases=def_alias).convert("\|a|")
    assert result == "<p>|a|</p>"

    result = MetaMarkdown(aliases=def_alias).convert("*|a|")
    assert result == "<p>*b</p>"

    result = MetaMarkdown(aliases=def_alias).convert("\|undefined|")
    assert result == "<p>|undefined|</p>"


def test_sub_alias_with_equals():
    result = MetaMarkdown(aliases={"a": "b=c"}).convert("|a|")

    assert result == "<p>b=c</p>"


def test_sub_alias_in_table():
    text = dedent(
        """
        |Table Col 1| Table Col 2 |
        |-----------| ----------- |
        |normal| entry |
        | [link](|page|/subpage2.html) | |other| |
        """
    )

    result = MetaMarkdown(
        aliases={"page": "/home/page", "other": "some alias"}
    ).convert(text)

    assert "[link]" not in result
    assert 'href="/home/page/subpage2.html"' in result
    assert "some alias" in result


def test_fix_relative_paths(tmp_path):
    base_path = tmp_path / "output"
    md = MetaMarkdown(base_url=tmp_path / "output")

    text = f"[link to thing]({base_path / 'thing'})"
    result = md.convert(text, path=base_path / "other")

    assert "../thing" in result
