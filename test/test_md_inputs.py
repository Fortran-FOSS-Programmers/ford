import pathlib
import re
import sys
from typing import List

import ford
import ford.fortran_project

from bs4 import BeautifulSoup

# Ford default src folder
DEFAULT_SRC = "src"


def run_ford(monkeypatch, md_file: pathlib.Path, extra_args: list = None):
    """Modify command line args with argv"""
    with monkeypatch.context() as m:
        command = ["ford", str(md_file)]
        if extra_args is not None:
            command = command[:1] + extra_args + command[1:]
        m.setattr(sys, "argv", command)
        ford.run()


def test_extra_mods_empty(
    copy_fortran_file,
    copy_settings_file,
    monkeypatch,
    restore_macros,
    restore_nameselector,
):
    """This checks that extra_mods is parsed correctly in input md file"""

    data = """\
    module test
    end module test
    """
    settings = """\
    search: false
    extra_mods:
    """

    copy_fortran_file(data)
    md_file = copy_settings_file(settings)

    run_ford(monkeypatch, md_file)


def test_extra_mods_intrinsic(
    copy_fortran_file,
    copy_settings_file,
    monkeypatch,
    restore_macros,
    restore_nameselector,
):
    """This checks that adding extra_mods doesn't change the module variable INTRINSIC_MODS"""
    data = """\
    module test
    end module test
    """
    settings = """\
    search: false
    extra_mods: dummy: dummy_module
    """
    # Initial value of intrinsic mods
    old_intrinsic_mods = ford.fortran_project.INTRINSIC_MODS.copy()

    # set up project data
    copy_fortran_file(data)
    md_file = copy_settings_file(settings)

    run_ford(monkeypatch, md_file)

    # Check that the module level variable has not been changed
    assert ford.fortran_project.INTRINSIC_MODS == old_intrinsic_mods


def get_main_body_text(html_dir: pathlib.Path, filename: str) -> List[str]:
    with open(html_dir / filename, "r") as f:
        index_html = BeautifulSoup(f.read(), features="html.parser")
    return index_html.find_all(string=re.compile("Test:"))


def test_default_aliases(
    copy_fortran_file,
    copy_settings_file,
    tmp_path,
    monkeypatch,
    restore_macros,
    restore_nameselector,
):
    """Check that aliases specified in project file are replaced correctly"""

    data = """\
    module test
    !! Test: The project media url (|media|) should work here too
    end module test
    """
    settings = """\
    search: false

    Test: The project media url should be |media|
    """

    copy_fortran_file(data)
    md_file = copy_settings_file(settings)

    run_ford(monkeypatch, md_file)

    html_dir = tmp_path / "doc"
    index_text = get_main_body_text(html_dir, "index.html")
    expected_index_text = [
        "Test: The project media url should be ./media",
    ]
    assert index_text == expected_index_text

    module_text = get_main_body_text(html_dir, "module/test.html")
    expected_module_text = [
        "Test: The project media url (./media) should work here too"
    ]
    assert module_text == expected_module_text


def test_one_alias(
    copy_fortran_file,
    copy_settings_file,
    tmp_path,
    monkeypatch,
    restore_macros,
    restore_nameselector,
):
    """Check that aliases specified in project file are replaced correctly"""

    data = """\
    module test
    !! Title
    !!
    !! Test: This foo should not be exanded
    !!
    !! Test: But this |foo| should be 'bar'
    end module test
    """
    settings = """\
    search: false
    alias: foo = bar

    Test: This |foo| should be expanded as 'bar'

    Test: This foo should not be.
    """

    copy_fortran_file(data)
    md_file = copy_settings_file(settings)

    run_ford(monkeypatch, md_file)

    html_dir = tmp_path / "doc"
    paragraphs = get_main_body_text(html_dir, "index.html")
    expected_paragraphs = [
        "Test: This bar should be expanded as 'bar'",
        "Test: This foo should not be.",
    ]
    assert paragraphs == expected_paragraphs

    module_text = get_main_body_text(html_dir, "module/test.html")
    expected_module_text = [
        "Test: This foo should not be exanded",
        "Test: But this bar should be 'bar'",
    ]
    assert module_text == expected_module_text


def test_multiple_aliases(
    copy_fortran_file,
    copy_settings_file,
    tmp_path,
    monkeypatch,
    restore_macros,
    restore_nameselector,
):
    """Check that aliases specified in project file are replaced correctly"""

    data = """\
    module test
    !! Title
    !!
    !! Test: This foo and zing should not be exanded
    !!
    !! Test: But this |foo| should be 'bar', and this |zing| 'quaff'
    end module test
    """
    settings = """\
    search: false
    alias: foo = bar
           zing = quaff

    Test: This |foo| should be expanded as 'bar', while |zing| should be 'quaff'

    Test: This foo and zing should not be.
    """

    copy_fortran_file(data)
    md_file = copy_settings_file(settings)

    run_ford(monkeypatch, md_file)

    html_dir = tmp_path / "doc"
    paragraphs = get_main_body_text(html_dir, "index.html")
    expected_paragraphs = [
        "Test: This bar should be expanded as 'bar', while quaff should be 'quaff'",
        "Test: This foo and zing should not be.",
    ]

    assert paragraphs == expected_paragraphs

    module_text = get_main_body_text(html_dir, "module/test.html")
    expected_module_text = [
        "Test: This foo and zing should not be exanded",
        "Test: But this bar should be 'bar', and this quaff 'quaff'",
    ]
    assert module_text == expected_module_text
