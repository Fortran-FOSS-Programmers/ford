# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 20:21:05 2020

@author: Peter M. Clausen
"""

import glob
import re

import ford.reader as reader

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
