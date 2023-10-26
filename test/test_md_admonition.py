import markdown
from textwrap import dedent

from ford.md_admonition import AdmonitionExtension, FordMarkdownError

from bs4 import BeautifulSoup
import pytest


def convert(text: str) -> str:
    md = markdown.Markdown(extensions=[AdmonitionExtension()], output_format="html")
    return md.convert(dedent(text))


def not_title(tag):
    return tag.name == "p" and not tag.has_attr("class")


def test_basic():
    converted = convert(
        """
        @note note text
        """
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 1
    assert sorted(soup.div["class"]) == ["alert", "alert-info"]
    assert soup.find(class_="h4").text == "Note"
    assert soup.div.find(not_title).text == "note text"


def test_uppercase():
    converted = convert(
        """
        @NOTE note text
        """
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 1
    assert sorted(soup.div["class"]) == ["alert", "alert-info"]
    assert soup.find(class_="h4").text == "Note"
    assert soup.div.find(not_title).text == "note text"


def test_endnote():
    converted = convert(
        """
        @note note text @endnote
        """
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 1
    assert sorted(soup.div["class"]) == ["alert", "alert-info"]
    assert soup.find(class_="h4").text == "Note"
    assert soup.div.find(not_title).text == "note text"


def test_paragraph():
    converted = convert(
        """
        @note note text
        some following text
        """
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 1
    assert sorted(soup.div["class"]) == ["alert", "alert-info"]
    assert soup.find(class_="h4").text == "Note"
    assert soup.div.find(not_title).text == "note text\nsome following text"


def test_paragraph_end_line():
    converted = convert(
        """
        @note note text
        some following text"""
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 1
    assert sorted(soup.div["class"]) == ["alert", "alert-info"]
    assert soup.find(class_="h4").text == "Note"
    assert soup.div.find(not_title).text == "note text\nsome following text"


def test_explicit_end():
    converted = convert(
        """
        @note note text
        some blank lines


        before the end
        @endnote
        """
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 1
    assert sorted(soup.div["class"]) == ["alert", "alert-info"]
    assert soup.find(class_="h4").text == "Note"
    assert soup.div.text.strip() == "Note\nnote text\nsome blank lines\nbefore the end"


def test_explicit_end_no_newline():
    converted = convert(
        """
        @note note text
        some blank lines


        before the end
        @endnote"""
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 1
    assert sorted(soup.div["class"]) == ["alert", "alert-info"]
    assert soup.find(class_="h4").text == "Note"
    assert soup.div.text.strip() == "Note\nnote text\nsome blank lines\nbefore the end"


def test_warning():
    converted = convert(
        """
        @warning note text
        """
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 1
    assert sorted(soup.div["class"]) == ["alert", "alert-warning"]
    assert soup.find(class_="h4").text == "Warning"
    assert soup.div.find(not_title).text == "note text"


def test_in_list():
    converted = convert(
        """
        - item 1

            @note note text

        - item 2
        """
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 1
    assert sorted(soup.div["class"]) == ["alert", "alert-info"]
    assert soup.find(class_="h4").text == "Note"
    assert soup.div.find(not_title).text == "note text"


def test_in_list_with_paragraph():
    converted = convert(
        """
        - item 1

            @note note text
            with a paragraph

            but not this one

        - item 2
        """
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 1
    assert sorted(soup.div["class"]) == ["alert", "alert-info"]
    assert soup.find(class_="h4").text == "Note"
    assert soup.div.find(not_title).text == "note text\nwith a paragraph"


def test_in_list_with_paragraph_and_end():
    converted = convert(
        """
        - item 1

            @note note text
            with a paragraph

            and another one
            @endnote

        - item 2
        """
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 1
    assert sorted(soup.div["class"]) == ["alert", "alert-info"]
    assert soup.find(class_="h4").text == "Note"
    all_text = "\n".join(p.text for p in soup.div.find_all(not_title))
    assert all_text == "note text\nwith a paragraph\nand another one"


def test_in_list_with_list():
    converted = convert(
        """
        - item 1

            @note note text

            1. first
            2. second

            @endnote

        - item 2
        """
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 1
    assert sorted(soup.div["class"]) == ["alert", "alert-info"]
    assert soup.find(class_="h4").text == "Note"
    list_text = " ".join(li.text for li in soup.div.ol.find_all("li"))
    assert list_text == "first second"


# The following test doesn't currently work, but could be supported by
# keeping track of a stack of admonitions. PRs welcome!

# def test_in_list_with_nested_warning():
#     converted = convert(
#         """
#         - item 1

#             @note note text
#             with a paragraph

#                 @warning nested warning

#             unnested paragraph
#             @endnote

#         - item 2
#         """
#     )

#     soup = BeautifulSoup(converted, features="html.parser")
#     assert len(soup) == 1
#     assert sorted(soup.div["class"]) == ["alert", "alert-info"]
#     assert soup.find(class_="h4").text == "Note"

#     nested_box = soup.div.div.extract()
#     assert nested_box.find(class_="h4").text == "Warning"
#     assert nested_box.find(not_title).text == "nested warning"

#     all_text = "\n".join(p.text for p in soup.div.find_all(not_title))
#     assert all_text == "note text\nwith a paragraph\nunnested paragraph"


def test_midparagraph():
    converted = convert(
        """
        @Bug start text

        end text @endbug post text
        """
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 3
    assert sorted(soup.div["class"]) == ["alert", "alert-danger"]
    assert soup.find(class_="h4").text == "Bug"
    all_text = "\n".join(p.text for p in soup.div.find_all(not_title))
    assert all_text == "start text\nend text"

    soup.div.extract()
    assert soup.text.strip() == "post text"


def test_title():
    converted = convert(
        """
        @warning some "title" text
        over multiple lines"""
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 1
    assert sorted(soup.div["class"]) == ["alert", "alert-warning"]
    assert soup.div.find(not_title).text == 'some "title" text\nover multiple lines'


def test_end_marker_without_start():
    with pytest.raises(FordMarkdownError):
        convert("@endnote")


def test_end_marker_doesnt_match_start():
    with pytest.raises(FordMarkdownError):
        convert("@bug\n@endnote")
