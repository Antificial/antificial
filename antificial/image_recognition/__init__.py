#! /usr/bin/env python

from .handler import run

# Use this to set us up if called directly
def main():
    print("This is the IR module reporting...")
    run()

if __name__ == '__main__':
    main()
