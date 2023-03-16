import ford
from textwrap import dedent
import sys
import pytest

from conftest import gfortran_is_not_installed


def test_quiet_false():
    """This checks that bool options like 'quiet' are parsed correctly in input md file"""

    data, _, _ = ford.parse_arguments({}, "quiet: false")
    assert data["quiet"] is False
    data, _, _ = ford.parse_arguments({}, "quiet: TRUE")
    assert data["quiet"] is True


def test_quiet_command_line():
    """Check that setting --quiet on the command line overrides project file"""

    data, _, _ = ford.parse_arguments({"quiet": True}, "quiet: false")
    assert data["quiet"] is True
    data, _, _ = ford.parse_arguments({"quiet": False}, "quiet: true")
    assert data["quiet"] is False


def test_list_input():
    """Check that setting a non-list option is turned into a single string"""

    settings = """\
    include: line1
             line2
    summary: This
             is
             one
             string
    """
    data, _, _ = ford.parse_arguments({}, dedent(settings))

    assert len(data["include"]) == 2
    assert data["summary"] == "This\nis\none\nstring"


def test_path_normalisation():
    """Check that paths get normalised correctly"""

    settings = """\
    page_dir: my_pages
    src_dir: src1
             src2
    """
    data, _, _ = ford.parse_arguments({}, dedent(settings), "/prefix/path")
    assert str(data["page_dir"]) == "/prefix/path/my_pages"
    assert [str(p) for p in data["src_dir"]] == [
        "/prefix/path/src1",
        "/prefix/path/src2",
    ]


def test_source_not_subdir_output():
    """Check if the src_dir is correctly detected as being a subdirectory of output_dir"""

    # This should be fine
    data, _, _ = ford.parse_arguments(
        {"src_dir": ["/1/2/3", "4/5"], "output_dir": "/3/4"}, "", "/prefix"
    )

    # This shouldn't be
    with pytest.raises(ValueError):
        data, _, _ = ford.parse_arguments(
            {"src_dir": ["4/5", "/1/2/3"], "output_dir": "/1/2"}, "", "/prefix"
        )
    # src_dir == output_dir
    with pytest.raises(ValueError):
        data, _, _ = ford.parse_arguments(
            {"src_dir": ["/1/2/"], "output_dir": "/1/2"}, "", "/prefix"
        )


def test_repeated_docmark():
    """Check that setting --quiet on the command line overrides project file"""

    settings = """\
    docmark: !
    predocmark: !
    """

    with pytest.raises(ValueError):
        ford.parse_arguments({}, dedent(settings))

    settings = """\
    docmark: !<
    predocmark_alt: !<
    """

    with pytest.raises(ValueError):
        ford.parse_arguments({}, dedent(settings))

    settings = """\
    docmark_alt: !!
    predocmark_alt: !!
    """

    with pytest.raises(ValueError):
        ford.parse_arguments({}, dedent(settings))


def test_no_preprocessor():
    data, _, _ = ford.parse_arguments({}, "preprocess: False")

    assert data["fpp_extensions"] == []


def test_bad_preprocessor():
    class FakeFile:
        name = "test file"

    with pytest.raises(SystemExit):
        ford.parse_arguments({"project_file": FakeFile()}, "preprocessor: false")


def test_maybe_ok_preprocessor():
    data, _, _ = ford.parse_arguments({}, "preprocessor: true")

    if data["preprocess"] is True:
        assert isinstance(data["preprocessor"], list)
        assert len(data["preprocessor"]) > 0


@pytest.mark.skipif(
    gfortran_is_not_installed(), reason="Requires gfortran to be installed"
)
def test_gfortran_preprocessor():
    data, _, _ = ford.parse_arguments({}, "preprocessor: gfortran -E")

    assert data["preprocess"] is True


def test_absolute_src_dir(monkeypatch, tmp_path):
    project_file = tmp_path / "example.md"
    project_file.touch()
    src_dir = tmp_path / "not_here"

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["ford", str(project_file)])
        args, _, _ = ford.initialize()

    assert args["src_dir"] == [tmp_path / "./src"]

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["ford", str(project_file), "--src_dir", str(src_dir)])
        args, _, _ = ford.initialize()

    assert args["src_dir"] == [src_dir]

    with monkeypatch.context() as m:
        m.setattr(
            sys, "argv", ["ford", "--src_dir", str(src_dir), "--", str(project_file)]
        )
        args, _, _ = ford.initialize()

    assert args["src_dir"] == [src_dir]


def test_output_dir_cli(monkeypatch, tmp_path):
    project_file = tmp_path / "example.md"
    project_file.touch()

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["ford", str(project_file), "--output_dir", "something"])
        settings, _, _ = ford.initialize()

    assert settings["output_dir"] == tmp_path / "something"

    with open(project_file, "w") as f:
        f.write("output_dir: something_else")

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["ford", str(project_file)])
        settings, _, _ = ford.initialize()

    assert settings["output_dir"] == tmp_path / "something_else"
