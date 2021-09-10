# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 20:21:05 2020

@author: Peter M. Clausen
"""

import glob
import re

import ford.reader as reader
from ford.reader import _contains_unterminated_string

RE_WHITE = re.compile(r"\s+")


def remove_multiple_white_space(lines):
    return [RE_WHITE.sub(" ", line.strip()) for line in lines]


def test_reader_test_data():
    """Basic regression test"""
    f_files = glob.glob("./test_data/*.f*")
    f_files = [
        f
        for f in f_files
        if "expected" not in f and "bad" not in f  # remove 'expected' and 'bad' files
    ]
    # Set to True to update the 'expected' files
    create_expected = False
    for ff in f_files:
        ee = ff.replace(".f90", "_expected.f90")
        print("\tProcessing: %s \tExpected: %s " % (ff, ee))
        lines = [
            line
            for line in reader.FortranReader(
                ff, docmark="!", predocmark=">", docmark_alt="#", predocmark_alt="<"
            )
        ]
        if create_expected:
            print("WARNING : Writing expected file " + ee)
            with open(ee, "w") as ef:
                for line in lines:
                    print(line)
                    ef.write(line + "\n")
        else:
            with open(ee) as ef:
                lines = remove_multiple_white_space(lines)
                elines = remove_multiple_white_space(ef.readlines())
                assert lines == elines


def test_reader_continuation(copy_fortran_file):
    """Checks that line continuations are handled correctly"""

    data = """\
    program foo
    !! some docs
    integer :: bar = &
    &
    4
    end
    """

    filename = copy_fortran_file(data)

    lines = list(reader.FortranReader(filename, docmark="!"))
    assert lines == ["program foo", "!! some docs", "integer :: bar = 4", "end"]


def test_type(copy_fortran_file):
    """Check that types can be read"""

    data = """\
    program foo
    !! base type
    type :: base
    end type base

    !! derived type
    type, extends(base) :: derived
    end type
    """

    expected = [
        "program foo",
        "!! base type",
        "type :: base",
        "end type base",
        "!! derived type",
        "type, extends(base) :: derived",
        "end type",
    ]

    filename = copy_fortran_file(data)

    lines = list(reader.FortranReader(filename, docmark="!"))
    assert lines == expected


def test_unknown_include(copy_fortran_file):
    """Check that `include "file.h"` ignores unknown files"""

    data = """\
    program test
    include "file.h"
    end program test
    """

    expected = [
        "program test",
        'include "file.h"',
        "end program test",
    ]

    filename = copy_fortran_file(data)

    lines = list(reader.FortranReader(filename, docmark="!"))
    assert lines == expected


def test_unterminated_strings():
    """Check the utility function works"""
    assert _contains_unterminated_string(""" bad "quote """)
    assert _contains_unterminated_string(""" bad 'quote """)
    assert _contains_unterminated_string(""" bad "'quote """)
    assert _contains_unterminated_string(""" bad 'quote" """)
    assert _contains_unterminated_string(""" "multiple" bad "'quote """)
    assert _contains_unterminated_string(""" bad 'quote" """)

    assert not _contains_unterminated_string(""" good "quote" """)
    assert not _contains_unterminated_string(""" good 'quote' """)
    assert not _contains_unterminated_string(""" good "'quote" """)
    assert not _contains_unterminated_string(""" good 'quote"' """)
    assert not _contains_unterminated_string(""" "multiple" good "'quote" """)
    assert not _contains_unterminated_string(""" good 'quote"' """)


def test_multiline_string(copy_fortran_file):
    """Check that we can continue string literals including exclamation
    marks over multiple lines. Issue #320"""

    data = '''\
    program multiline_string
      implicit none
      print*, 'dont''t', " get ""!>quotes!@""", " '""!<wrong!!""' ", "foo&
              &bar! foo&
              &bar"
    end program multiline_string
    '''

    filename = copy_fortran_file(data)
    expected = [
        "program multiline_string",
        "implicit none",
        '''print*, 'dont''t', " get ""!>quotes!@""", " '""!<wrong!!""' ", "foobar! foobar"''',
        "end program multiline_string",
    ]

    lines = list(
        reader.FortranReader(
            filename, docmark="!", predocmark="<", docmark_alt=">", predocmark_alt="@"
        )
    )
    assert lines == expected
