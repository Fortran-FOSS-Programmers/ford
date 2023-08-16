import pytest
from textwrap import dedent
import ford
from ford.utils import meta_preprocessor


@pytest.mark.parametrize("string", ["true", "True", "TRUE", "tRuE"])
def test_str_to_bool_true(string):
    assert ford.utils.str_to_bool(string)


@pytest.mark.parametrize("string", ["false", "False", "FALSE", "fAlSe"])
def test_str_to_bool_false(string):
    assert not ford.utils.str_to_bool(string)


def test_str_to_bool_already_bool():
    assert ford.utils.str_to_bool(True)
    assert not ford.utils.str_to_bool(False)


@pytest.mark.parametrize(
    ("string", "level", "expected"),
    [
        ("abcdefghi", 0, ["abcdefghi"]),
        ("abc(def)ghi", 1, ["(def)"]),
        ("abc(def)ghi", 0, ["abc()ghi"]),
        ("(abc)def(ghi)", 1, ["(abc)", "(ghi)"]),
        ("(a(b)c)def(gh(i))", 1, ["(a()c)", "(gh())"]),
    ],
)
def test_strip_paren(string, level, expected):
    assert ford.utils.strip_paren(string, retlevel=level) == expected


def test_meta_preprocessor():
    text = dedent(
        """\
    key1: value1
    key2: value2
          value2a
    key3: value3

    no more metadata"""
    )

    meta, doc = meta_preprocessor(text)

    assert doc == ["no more metadata"]
    assert meta == {
        "key1": ["value1"],
        "key2": ["value2", "value2a"],
        "key3": ["value3"],
    }
