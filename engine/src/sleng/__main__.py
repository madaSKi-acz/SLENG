"""
Purpose:  `python -m sleng ...` runs the same command line as the `sleng` script.
Layer:    sleng (entry point)
Exports:  nothing
Depends:  sleng.adapters.cli
"""

import sys

from sleng.adapters.cli import main

sys.exit(main())
