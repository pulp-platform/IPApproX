#!/usr/bin/env python
# KISS script to load configuration files from IPs

from vsim_defines   import *
from vivado_defines import *
import sys

# returns true if source file is VHDL
def is_vhdl(f):
    if f[-4:] == ".vhd":
        return True
    else:
        return False

# list of allowed and mandatory keys for the Yaml dictionary
ALLOWED_KEYS = [
    'incdirs',
    'vlog_opts',
    'vcom_opts',
    'tech',
    'targets'
]
MANDATORY_KEYS = [
    'files'
]

# list of allowed targets
ALLOWED_TARGETS = [
    'all',
    'xilinx',
    'rtl'
]

class SubIPConfig(object):
    def __init__(self, ip_name, sub_ip_name, sub_ip_dic, ip_path):
        super(SubIPConfig, self).__init__()

        self.ip_name     = ip_name
        self.ip_path     = ip_path
        self.sub_ip_name = sub_ip_name
        self.sub_ip_dic  = sub_ip_dic

        self.__check_dic()
        self.files     = self.__get_files()     # list of source files in the sub-IP
        self.targets   = self.__get_targets()   # target (all, rtl or fpga at the moment)
        self.incdirs   = self.__get_incdirs()   # verilog include directory
        self.tech      = self.__get_tech()      # if True, do not generate analyze scripts for this ip :)
        self.vlog_opts = self.__get_vlog_opts() # generic vlog options
        self.vcom_opts = self.__get_vcom_opts() # generic vcom options

    def export_vsim(self, abs_path, more_opts, target_tech='st28fdsoi'):
        if not ("all" in self.targets or "rtl" in self.targets):
            return "\n"
        vlog_cmd = VSIM_PREAMBLE_SUBIP % (self.sub_ip_name)
        files = self.files
        vlog_includes = ""
        for i in self.incdirs:
            vlog_includes += "%s%s/%s" % (VSIM_VLOG_INCDIR_CMD, abs_path, i)
        for f in files:
            if not is_vhdl(f):
                vlog_cmd += VSIM_VLOG_CMD % ("%s %s" % (more_opts, self.vlog_opts), vlog_includes, "%s/%s" % (abs_path, f))
            else:
                vlog_cmd += VSIM_VCOM_CMD % ("%s %s" % (more_opts, self.vcom_opts), "%s/%s" % (abs_path, f))
        return vlog_cmd
        
    def export_vivado(self, abs_path, more_opts):
        if not ("all" in self.targets or "xilinx" in self.targets):
            return "\n"
        vivado_cmd = VIVADO_PREAMBLE_SUBIP % (self.sub_ip_name, self.sub_ip_name.upper())
        files = self.files
        for f in files:
            vivado_cmd += "    %s/%s/%s \\\n" % (abs_path, self.ip_path, f)
        vivado_cmd += VIVADO_POSTAMBLE_SUBIP
        if len(self.incdirs) > 0:
            vivado_cmd += VIVADO_PREAMBLE_SUBIP_INCDIRS % (self.sub_ip_name.upper())
            for i in self.incdirs:
                vivado_cmd += "    %s/%s/%s \\\n" % (abs_path, self.ip_path, i)
            vivado_cmd += VIVADO_POSTAMBLE_SUBIP
        return vivado_cmd
        
    def export_synplify(self, abs_path, more_opts):
        if not ("all" in self.targets or "xilinx" in self.targets):
            return "\n"
        synplify_cmd = ""
        files = self.files
        if len(files) == 0:
            files.extend(self.files)
        for f in files:
            if not is_vhdl(f):
                synplify_cmd += "add_file -verilog %s/%s/%s\n" % (abs_path, self.ip_path, f)
            else:
                synplify_cmd += "add_file -vhdl %s/%s/%s\n" % (abs_path, self.ip_path, f)
        return synplify_cmd

    ### management of the Yaml dictionary

    def __check_dic(self):
        dic = self.sub_ip_dic
        if set(MANDATORY_KEYS).intersection(set(dic.keys())) == set([]):
            print "ERROR: there are no files for ip '%s', sub-ip '%s'. Check its src_files.yml file." % (self.ip_name, self.sub_ip_name)
            sys.exit(1)
        not_allowed = set(dic.keys()) - set(MANDATORY_KEYS) - set(ALLOWED_KEYS)
        if not_allowed != set([]):
            print "ERROR: there are unallowed keys for ip '%s', sub-ip '%s':" % (self.ip_name, self.sub_ip_name)
            for el in list(not_allowed):
                print "    %s" % el
            print "Check the src_files.yml file."
            sys.exit(1)

    def __get_files(self):
        return self.sub_ip_dic['files']

    def __get_targets(self):
        try:
            targets = self.sub_ip_dic['targets']
        except KeyError:
            targets = ["all"]
        not_allowed = set(targets) - (set(ALLOWED_TARGETS))
        if not_allowed != set([]):
            print "ERROR: targets not allowed for ip '%s', sub-ip '%s':" % (self.ip_name, self.sub_ip_name)
            print not_allowed
            for el in list(not_allowed):
                print "    %s" % el
            print "Check the src_files.yml file."
            sys.exit(1)
        return targets

    def __get_incdirs(self):
        try:
            incdirs = self.sub_ip_dic['incdirs']
        except KeyError:
            incdirs = []
        return incdirs

    def __get_tech(self):
        try:
            tech = self.sub_ip_dic['tech']
        except KeyError:
            tech = False
        return tech

    def __get_vlog_opts(self):
        try:
            vlog_opts = " ".join(self.sub_ip_dic['vlog_opts'])
        except KeyError:
            vlog_opts = ""
        return vlog_opts

    def __get_vcom_opts(self):
        try:
            vcom_opts = " ".join(self.sub_ip_dic['vcom_opts'])
        except KeyError:
            vcom_opts = ""
        return vcom_opts

