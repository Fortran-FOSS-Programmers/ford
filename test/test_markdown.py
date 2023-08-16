from ford._markdown import MetaMarkdown


def test_sub_alias():
    result = MetaMarkdown(aliases={"a": "b"}).convert("|a|")

    assert result == "<p>b</p>"


def test_sub_alias_with_equals():
    result = MetaMarkdown(aliases={"a": "b=c"}).convert("|a|")

    assert result == "<p>b=c</p>"
