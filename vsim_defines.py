#!/usr/bin/env python
# KISS script to load configuration files from IPs

VSIM_PREAMBLE = """#!/bin/tcsh
source ${IPS_PATH}/scripts/colors.sh

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
