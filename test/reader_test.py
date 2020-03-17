# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 20:21:05 2020

@author: xr3
"""

import unittest
import glob
import re

RE_WHITE=re.compile(r'\s+')

#import sys
#sys.path.append('./ford')

import ford.reader as reader


def remove_multiple_white_space(lines):
    return [RE_WHITE.sub(' ',line.strip()) for line in lines]

class Test_reader(unittest.TestCase):
    def test_reader_test_data(self):
        f_files = glob.glob('./test_data/*.f*')
        f_files = [f for f in f_files 
                       if  not 'expected' in f # remove 'expected' files
                       and not 'bad' in f]     # remove 'bad files' 
        #create_expected=True
        create_expected=False
        for ff in f_files:
            ee=ff.replace('.f90','_expected.f90')
            print('\tProcessing: %s \tExpected: %s '%(ff,ee))
            lines=[line for line in reader.FortranReader(ff,docmark='!',predocmark='>',docmark_alt='#',predocmark_alt='<') ]
            if create_expected:
                print('WARNING : Writing expected file '+ee)
                with open(ee,'w') as ef:                    
                    for line in lines:
                        print(line) 
                        ef.write(line+'\n')
            else:
                with open(ee) as ef:
                    lines=remove_multiple_white_space(lines)
                    elines=remove_multiple_white_space(ef.readlines())
                    self.assertEqual(lines, elines)
        
                
if __name__ == '__main__':
    unittest.main()