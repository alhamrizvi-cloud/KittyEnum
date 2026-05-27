#!/usr/bin/env python3
"""KittyEnum alias entrypoint.

This script forwards execution to autoenum.py so you can use
`python3 kittyenum.py ...` or configure a shell alias/executable named
`kittyenum`.
"""

from autoenum import main

if __name__ == "__main__":
    main()
