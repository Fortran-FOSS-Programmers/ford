import ford
from textwrap import dedent
from pathlib import Path
import sys
import pytest

import tomli_w

from conftest import gfortran_is_not_installed


class FakeFile:
    name = "test file"


def test_quiet_false(tmp_path):
    _, data = ford.load_settings("quiet: False", tmp_path)
    assert data.quiet is False
    _, data2 = ford.load_settings("quiet: True", tmp_path)
    assert data2.quiet is True


def test_toml(tmp_path):
    settings_file = tmp_path / "fpm.toml"
    settings = {
        "extra": {
            "ford": {
                "quiet": True,
                "display": ["public", "protected"],
                "src_dir": "./source",
            }
        }
    }
    settings_file.write_text(tomli_w.dumps(settings))

    _, data = ford.load_settings("", tmp_path)

    assert data.quiet is True
    assert data.display[0] == "public"
    assert data.display[1] == "protected"
    assert data.src_dir == ["./source"]


def test_quiet_command_line():
    """Check that setting --quiet on the command line overrides project file"""

    data, _ = ford.parse_arguments(
        {"quiet": True, "preprocess": False}, "", ford.ProjectSettings(quiet=False)
    )
    assert data.quiet is True
    data, _ = ford.parse_arguments(
        {"quiet": False, "preprocess": False}, "", (ford.ProjectSettings(quiet=True))
    )
    assert data.quiet is False


def test_list_input(tmp_path):
    """Check that setting a non-list option is turned into a single string"""

    settings = """\
    include: line1
             line2
    summary: This
             is
             one
             string
    """
    _, data = ford.load_settings(dedent(settings), tmp_path)

    assert len(data.include) == 2
    assert data.summary == "This\nis\none\nstring"


def test_path_normalisation():
    """Check that paths get normalised correctly"""

    data, _ = ford.parse_arguments(
        {"preprocess": False},
        "",
        ford.ProjectSettings(page_dir="my_pages", src_dir=["src1", "src2"]),
        directory="/prefix/path",
    )
    assert data.page_dir == Path("/prefix/path/my_pages").absolute()
    assert data.src_dir == [
        Path("/prefix/path/src1").absolute(),
        Path("/prefix/path/src2").absolute(),
    ]


def test_source_not_subdir_output():
    """Check if the src_dir is correctly detected as being a subdirectory of output_dir"""

    # This should be fine
    data, _ = ford.parse_arguments(
        {"src_dir": ["/1/2/3", "4/5"], "output_dir": "/3/4", "preprocess": False},
        "",
        ford.ProjectSettings(),
        directory="/prefix",
    )

    # This shouldn't be
    with pytest.raises(ValueError):
        data, _ = ford.parse_arguments(
            {"src_dir": ["4/5", "/1/2/3"], "output_dir": "/1/2", "preprocess": False},
            "",
            ford.ProjectSettings(),
            directory="/prefix",
        )
    # src_dir == output_dir
    with pytest.raises(ValueError):
        data, _ = ford.parse_arguments(
            {"src_dir": ["/1/2/"], "output_dir": "/1/2", "preprocess": False},
            "",
            ford.ProjectSettings(),
            directory="/prefix",
        )


def test_repeated_docmark():
    """Check that setting --quiet on the command line overrides project file"""

    with pytest.raises(ValueError):
        ford.parse_arguments(
            {"preprocess": False},
            "",
            (ford.ProjectSettings(**{"docmark": "!", "predocmark": "!"})),
        )

    with pytest.raises(ValueError):
        ford.parse_arguments(
            {"preprocess": False},
            "",
            (ford.ProjectSettings(**{"docmark": "!<", "predocmark_alt": "!<"})),
        )

    with pytest.raises(ValueError):
        ford.parse_arguments(
            {"preprocess": False},
            "",
            (ford.ProjectSettings(**{"docmark_alt": "!!", "predocmark_alt": "!!"})),
        )


def test_no_preprocessor():
    data, _ = ford.parse_arguments(
        {}, "", (ford.ProjectSettings(**{"preprocess": False}))
    )

    assert data.fpp_extensions == []


def test_bad_preprocessor():
    with pytest.raises(SystemExit):
        ford.parse_arguments(
            {"project_file": FakeFile()},
            "",
            (ford.ProjectSettings(**{"preprocessor": "false"})),
        )


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="FIXME: Need portable do-nothing command"
)
def test_maybe_ok_preprocessor():
    data, _ = ford.parse_arguments(
        {}, "", (ford.ProjectSettings(**{"preprocessor": "true"}))
    )

    if data.preprocess is True:
        assert data.preprocessor == "true"


@pytest.mark.skipif(
    gfortran_is_not_installed(), reason="Requires gfortran to be installed"
)
def test_gfortran_preprocessor():
    data, _ = ford.parse_arguments(
        {}, "", (ford.ProjectSettings(**{"preprocessor": "gfortran -E"}))
    )

    assert data.preprocess is True


def test_absolute_src_dir(monkeypatch, tmp_path):
    project_file = tmp_path / "example.md"
    project_file.write_text("preprocess: False")
    src_dir = tmp_path / "not_here"

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["ford", str(project_file)])
        args, _ = ford.initialize()

    assert args.src_dir == [tmp_path / "./src"]

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["ford", str(project_file), "--src_dir", str(src_dir)])
        args, _ = ford.initialize()

    assert args.src_dir == [src_dir]

    with monkeypatch.context() as m:
        m.setattr(
            sys, "argv", ["ford", "--src_dir", str(src_dir), "--", str(project_file)]
        )
        args, _ = ford.initialize()

    assert args.src_dir == [src_dir]


def test_output_dir_cli(monkeypatch, tmp_path):
    project_file = tmp_path / "example.md"
    project_file.write_text("preprocess: False")

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["ford", str(project_file), "--output_dir", "something"])
        settings, _ = ford.initialize()

    assert settings.output_dir == tmp_path / "something"

    with open(project_file, "a") as f:
        f.write("\noutput_dir: something_else")

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["ford", str(project_file)])
        settings, _ = ford.initialize()

    assert settings.output_dir == tmp_path / "something_else"


def test_config_option():
    command_line_args = {
        "preprocess": False,
        "config": "quiet = true; display = ['public']; alias = {a = 'b', c = 'd'}",
    }

    data, _ = ford.parse_arguments(
        command_line_args, "", ford.ProjectSettings(quiet=False)
    )

    assert data.quiet is True
    assert data.display == ["public"]
    assert data.alias == {"a": "b", "c": "d"}


def test_external_links_command_line_arg():
    data, _ = ford.parse_arguments(
        {"external": "remote = https://some.link"}, "", ford.ProjectSettings()
    )

    assert data.external == {"remote": "https://some.link"}
