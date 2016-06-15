#!/usr/bin/env python
#
# vivado_defines.py
# Francesco Conti <f.conti@unibo.it>
#
# Copyright (C) 2015 ETH Zurich, University of Bologna
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.
#

VERILATOR_PREAMBLE = """#!/bin/tcsh

"""

VERILATOR_INCLUDES = """set VERILATOR_INCLUDES="%s" """

VERILATOR_COMMAND = """

verilator +1800-2012ext+ -cc %s $VERILATOR_INCLUDES

"""

