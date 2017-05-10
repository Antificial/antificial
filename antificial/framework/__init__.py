#! /usr/bin/env python

# Import all modules to be directly available when this module is loaded
from .handler import run
from .colony import *
from .world import *

# Use this to set us up if called directly
def main():
    print("This is the FW module reporting...")

if __name__ == '__main__':
    main()
