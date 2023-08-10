from ford.settings import is_same_type, Settings, load_markdown_settings

from typing import List, Optional
from textwrap import dedent
import pytest


@pytest.mark.parametrize(
    ("type_in", "tp", "expected"),
    (
        (list, list, True),
        (list, str, False),
        (List[str], list, True),
        (Optional[str], str, True),
    ),
)
def test_is_same_type(type_in, tp, expected):
    assert is_same_type(type_in, tp) is expected


def test_settings_type_conversion():
    settings = Settings(src_dir="./src")

    assert settings.src_dir == ["./src"]


def test_settings_type_conversion_from_markdown():
    settings, _ = load_markdown_settings(
        ".",
        dedent(
            """\
            ---
            project: some project
            src_dir: source
            summary: first
                     second
            preprocess: true
            fpp_extensions: fpp
                            F90
            max_frontpage_items: 4
            ---
            """
        ),
    )

    assert settings.src_dir == ["source"]
    assert settings.fpp_extensions == ["fpp", "F90"]
    assert settings.project == "some project"
    assert settings.summary == "first\nsecond"
    assert settings.preprocess is True
    assert settings.max_frontpage_items == 4
