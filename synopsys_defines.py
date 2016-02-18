#!/usr/bin/env python
# KISS script to load configuration files from IPs

# templates for vcompile.csh scripts

SYNOPSYS_ANALYZE_PREAMBLE = "### analyze script for %s ip\n"

SYNOPSYS_ANALYZE_PREAMBLE_SUBIP = "\n# compile %s\n"

SYNOPSYS_ANALYZE_SV_CMD   = "analyze -format sverilog -work work ${IPS_PATH}/%s\n"
SYNOPSYS_ANALYZE_V_CMD    = "analyze -format verilog  -work work ${IPS_PATH}/%s\n"
SYNOPSYS_ANALYZE_VHDL_CMD = "analyze -format vhdl     -work work ${IPS_PATH}/%s\n"
