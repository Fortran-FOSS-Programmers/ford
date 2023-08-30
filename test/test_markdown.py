from ford._markdown import MetaMarkdown


def test_sub_alias():
    result = MetaMarkdown(aliases={"a": "b"}).convert("|a|")

    assert result == "<p>b</p>"


def test_sub_alias_with_equals():
    result = MetaMarkdown(aliases={"a": "b=c"}).convert("|a|")

    assert result == "<p>b=c</p>"


def test_fix_relative_paths(tmp_path):
    base_path = tmp_path / "output"
    md = MetaMarkdown(relative=True, base_url=tmp_path / "output")

    text = f"[link to thing]({base_path / 'thing'})"
    result = md.convert(text, path=base_path / "other")

    assert "../thing" in result
