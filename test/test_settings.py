from ford.settings import (
    is_same_type,
    ProjectSettings,
    load_markdown_settings,
    EntitySettings,
)

from typing import List, Optional
from textwrap import dedent
import pytest


@pytest.mark.parametrize(
    ("type_in", "tp", "expected"),
    (
        (list, list, True),
        (list, str, False),
        (List[str], List[str], True),
        (Optional[str], str, True),
    ),
)
def test_is_same_type(type_in, tp, expected):
    assert is_same_type(type_in, tp) is expected


def test_settings_type_conversion():
    settings = ProjectSettings(src_dir="./src")

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
            alias: a = b
                c = d
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
    assert settings.alias == {
        "a": "b",
        "c": "d",
        "url": ".",
        "media": "media",
        "page": "page",
    }


def test_entity_settings_from_project():
    project_settings = ProjectSettings(source=True)
    entity_settings = EntitySettings.from_project_settings(project_settings)
    assert entity_settings.source is True


def test_update_entity_settings():
    expected_version = "1.0.1"
    settings = EntitySettings(source=True)
    settings.update({"version": expected_version})

    assert settings.source is True
    assert settings.version == expected_version
