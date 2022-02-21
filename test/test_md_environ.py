import os
import markdown

from ford.md_environ import EnvironExtension


def test_md_environ():
    md = markdown.Markdown(
        extensions=[EnvironExtension()],
        output_format="html5",
    )

    expected_text = "success"
    os.environ["FORD_TEST_ENV_VAR"] = expected_text

    converted = md.convert("${FORD_TEST_ENV_VAR}")

    assert converted == f"<p>{expected_text}</p>"
