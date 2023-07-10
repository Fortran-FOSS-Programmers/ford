import os
import markdown
from textwrap import dedent

from ford.md_admonition import AdmonitionExtension

from bs4 import BeautifulSoup
import pytest


def convert(text: str) -> str:
    md = markdown.Markdown(extensions=[AdmonitionExtension()], output_format="html")
    return md.convert(dedent(text))


def test_basic():
    converted = convert(
        """
        @note note text
        """
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 1
    assert sorted(soup.div["class"]) == ["alert", "alert-info"]
    assert soup.div["role"] == "alert"
    assert soup.h4.text == "Note"
    assert soup.div.p.text == "note text"


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
    assert soup.div["role"] == "alert"
    assert soup.h4.text == "Note"
    assert soup.div.p.text == "note text\nsome following text"


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
    assert soup.div["role"] == "alert"
    assert soup.h4.text == "Note"
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
    assert soup.div["role"] == "alert"
    assert soup.h4.text == "Warning"
    assert soup.div.p.text == "note text"


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
    assert soup.div["role"] == "alert"
    assert soup.h4.text == "Note"
    assert soup.div.p.text == "note text"


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
    assert soup.div["role"] == "alert"
    assert soup.h4.text == "Note"
    assert soup.div.p.text == "note text\nwith a paragraph"


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
    assert soup.div["role"] == "alert"
    assert soup.h4.text == "Note"
    all_text = "\n".join(p.text for p in soup.div.find_all("p"))
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
    assert soup.div["role"] == "alert"
    assert soup.h4.text == "Note"
    list_text = " ".join(li.text for li in soup.div.ol.find_all("li"))
    assert list_text == "first second"


def test_in_list_with_nested_warning():
    converted = convert(
        """
        - item 1

            @note note text
            with a paragraph

                @warning nested warning

            unnested paragraph
            @endnote

        - item 2
        """
    )

    soup = BeautifulSoup(converted, features="html.parser")
    assert len(soup) == 1
    assert sorted(soup.div["class"]) == ["alert", "alert-info"]
    assert soup.div["role"] == "alert"
    assert soup.h4.text == "Note"

    nested_box = soup.div.div.extract()
    assert nested_box.h4.text == "Warning"
    assert nested_box.p.text == "nested warning"

    all_text = "\n".join(p.text for p in soup.div.find_all("p"))
    assert all_text == "note text\nwith a paragraph\nunnested paragraph"
