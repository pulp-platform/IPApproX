#!/usr/bin/env python
# KISS script to load configuration files from IPs

# templates for vcompile.csh scripts
VSIM_PREAMBLE = """#!/bin/tcsh
source ${PULP_PATH}/fe/sim/vcompile/setup.csh

##############################################################################
# Settings
##############################################################################

set IP=%s

##############################################################################
# Check settings
##############################################################################

# check if environment variables are defined
if (! $?MSIM_LIBS_PATH ) then
  echo "${Red} MSIM_LIBS_PATH is not defined ${NC}"
  exit 1
endif

if (! $?IPS_PATH ) then
  echo "${Red} IPS_PATH is not defined ${NC}"
  exit 1
endif

set LIB_NAME="${IP}_lib"
set LIB_PATH="${MSIM_LIBS_PATH}/${LIB_NAME}"
set IP_PATH="${IPS_PATH}/%s"
set RTL_PATH="${RTL_PATH}"

##############################################################################
# Preparing library
##############################################################################

echo "${Green}--> Compiling ${IP}... ${NC}"

rm -rf $LIB_PATH

vlib $LIB_PATH
vmap $LIB_NAME $LIB_PATH

##############################################################################
# Compiling RTL
##############################################################################
"""

VSIM_POSTAMBLE ="""
echo "${Cyan}--> ${IP} compilation complete! ${NC}"
exit 0

##############################################################################
# Error handler
##############################################################################

error:
echo "${NC}"
exit 1
"""

VSIM_PREAMBLE_SUBIP = """
echo "${Green}Compiling component: ${Brown} %s ${NC}"
echo "${Red}"
"""
VSIM_VLOG_INCDIR_CMD = "+incdir+"
VSIM_VLOG_CMD = "vlog -quiet -sv -work ${LIB_PATH} %s %s %s || goto error\n"

VSIM_VCOM_CMD = "vcom -quiet -work ${LIB_PATH} %s %s || goto error\n"

# templates for vsim.tcl
VSIM_TCL_PREAMBLE = """set VSIM_IP_LIBS " \\\

"""

VSIM_TCL_CMD = "  -L %s_lib \\\n"

VSIM_TCL_POSTAMBLE = """"
"""

# templates for vcompile_libs.tc
VCOMPILE_LIBS_PREAMBLE = """#!/usr/bin/tcsh

echo \"\"
echo \"${Green}--> Compiling PULP IPs libraries... ${NC}\"
"""

VCOMPILE_LIBS_CMD = "tcsh ${PULP_PATH}/fe/sim/vcompile/ips/vcompile_%s.csh || exit 1\n"
