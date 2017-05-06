#! /usr/bin/env python

import sys

def iprint(s):
    print(s.format(**sys._getframe(1).f_locals)) # Get local variables of calling function and match them to names in the string
