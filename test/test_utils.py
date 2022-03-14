import pytest

import ford


def test_sub_macro(restore_macros):
    ford.utils.register_macro("a=b")
    result = ford.utils.sub_macros("|a|")

    assert result == "b"


def test_sub_macro_with_equals(restore_macros):
    ford.utils.register_macro("a=b=c")
    result = ford.utils.sub_macros("|a|")

    assert result == "b=c"


def test_register_macro_clash(restore_macros):
    ford.utils.register_macro("a=b")

    # Should be ok registering the same key-value pair again
    ford.utils.register_macro("a=b")

    with pytest.raises(RuntimeError):
        ford.utils.register_macro("a=c")


@pytest.mark.parametrize("string", ["true", "True", "TRUE", "tRuE"])
def test_str_to_bool_true(string):
    assert ford.utils.str_to_bool(string)


@pytest.mark.parametrize("string", ["false", "False", "FALSE", "fAlSe"])
def test_str_to_bool_false(string):
    assert not ford.utils.str_to_bool(string)


def test_str_to_bool_already_bool():
    assert ford.utils.str_to_bool(True)
    assert not ford.utils.str_to_bool(False)
