from ford.md_striped_table import StripedTableCSSExtension
import markdown
from bs4 import BeautifulSoup
import textwrap


def test_zebra_table():
    """Check that alternate rows have different classes"""
    md = markdown.Markdown(
        extensions=["markdown.extensions.extra", StripedTableCSSExtension()],
        output_format="html5",
    )

    text = textwrap.dedent(
        """
        | Header1    | Header2     |
        | ---------- | ----------- |
        | some text  | some text   |
        | some text  | some text   |
        | some text  | some text   |
        | some text  | some text   |
        """
    )

    html = md.convert(text)
    soup = BeautifulSoup(html, features="html.parser")

    print(soup)
    assert "table" in soup.table.attrs["class"]
    assert "table-striped" in soup.table.attrs["class"]


def test_no_clobber_html_table():
    """Check that tables with CSS already applied don't get modified"""
    md = markdown.Markdown(
        extensions=["markdown.extensions.extra", StripedTableCSSExtension()],
        output_format="html5",
    )

    text = textwrap.dedent(
        """
        <table class="dont-touch">
        <thead>
        <tr>
        <th>Header1</th>
        <th>Header2</th>
        </tr>
        </thead>
        <tbody>
        <tr class="row1">
        <td>some text</td>
        <td>some text</td>
        </tr>
        <tr class="row2">
        <td>some text</td>
        <td>some text</td>
        </tr>
        <tr class="row3">
        <td>some text</td>
        <td>some text</td>
        </tr>
        <tr class="row4">
        <td>some text</td>
        <td>some text</td>
        </tr>
        </tbody>
        </table>
        """
    )

    html = md.convert(text)
    soup = BeautifulSoup(html, features="html.parser")

    print(soup)
    assert soup.table.attrs["class"] == ["dont-touch"]

    body = soup.table.find("tbody")
    rows = body.find_all("tr")
    assert rows[0].attrs["class"] == ["row1"]
    assert rows[1].attrs["class"] == ["row2"]
    assert rows[2].attrs["class"] == ["row3"]
    assert rows[3].attrs["class"] == ["row4"]
