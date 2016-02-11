#!/usr/bin/env python
# KISS script to load configuration files from IPs

from vsim_defines   import *
from vivado_defines import *

class SubIPConfig(object):
    def __init__(self, ip_name, sub_ip_name, sub_ip_dic, ip_path):
        super(SubIPConfig, self).__init__()

        self.ip_name     = ip_name
        self.ip_path     = ip_path
        self.sub_ip_name = sub_ip_name

        try:
            self.incdirs = sub_ip_dic['incdirs']
        except KeyError:
            self.incdirs = []

        # target-specific source files for the IP (mutually exclusive)
        self.target_tech = 0
        self.target_rtl  = 0
        self.target_fpga = 0
        try:
            self.files_umc65_synth = sub_ip_dic['files_umc65_synth']
            self.target_tech += 1
        except KeyError:
            self.files_umc65_synth = []
        try:
            self.files_st28fdsoi_synth = sub_ip_dic['files_st28fdsoi_synth']
            self.target_tech += 1
        except KeyError:
            self.files_st28fdsoi_synth = []
        try:
            self.files_gf28_synth = sub_ip_dic['files_gf28_synth']
            self.target_tech += 1
        except KeyError:
            self.files_gf28_synth = []
        try:
            self.files_xilinx_synth = sub_ip_dic['files_xilinx_synth']
            self.target_fpga += 1
        except KeyError:
            self.files_xilinx_synth = []
        try:
            self.files_umc65 = sub_ip_dic['files_umc65']
            self.target_tech += 1
        except KeyError:
            self.files_umc65 = []
        try:
            self.files_st28fdsoi = sub_ip_dic['files_st28fdsoi']
            self.target_tech += 1
        except KeyError:
            self.files_st28fdsoi = []
        try:
            self.files_gf28 = sub_ip_dic['files_gf28']
            self.target_tech += 1
        except KeyError:
            self.files_gf28 = []
        try:
            self.files_xilinx = sub_ip_dic['files_xilinx']
            self.target_fpga += 1
        except KeyError:
            self.files_xilinx = []
        try:
            self.files_rtl = sub_ip_dic['files_rtl']
            self.target_rtl += 1
        except KeyError:
            self.files_rtl = []

        # generic source files of the IP (for all targets)
        try:
            self.files = sub_ip_dic['files']
            self.target_tech += 1
            self.target_rtl  += 1
            self.target_fpga += 1
        except KeyError:
            self.files = []

        if self.target_rtl+self.target_tech+self.target_fpga == 0:
            print "ERROR: there are no sources associated to ip %s, sub-ip %s. Check its src_files.yml file." % (ip_name, sub_ip_name)
            sys.exit(1)

        try:
            self.vhdl = sub_ip_dic['vhdl']
        except KeyError:
            self.vhdl = False

        try:
            self.more_opts = " ".join(sub_ip_dic['vsim_opts'])
        except KeyError:
            self.more_opts = ""

    def export_vsim(self, abs_path, more_opts, target_tech='st28fdsoi'):
        vlog_cmd = VSIM_PREAMBLE_SUBIP % (self.sub_ip_name)
        files = self.files[:]
        files.extend(self.files_rtl)
        if target_tech=='st28fdsoi':
            files.extend(self.files_st28fdsoi)
        elif target_tech=='umc65':
            files.extend(self.files_umc65)
        elif target_tech=='gf28':
            files.extend(self.files_gf28)
        if not self.vhdl:
            vlog_includes = ""
            for i in self.incdirs:
                vlog_includes += "%s%s/%s" % (VSIM_VLOG_INCDIR_CMD, abs_path, i)
            for f in files:
                vlog_cmd += VSIM_VLOG_CMD % ("%s %s" % (more_opts, self.more_opts), vlog_includes, "%s/%s" % (abs_path, f))
        else:
            for f in files:
                vlog_cmd += VSIM_VCOM_CMD % ("%s %s" % (more_opts, self.more_opts), "%s/%s" % (abs_path, f))
        return vlog_cmd
        
    def export_vivado(self, abs_path, more_opts):
        vivado_cmd = VIVADO_PREAMBLE_SUBIP % (self.sub_ip_name, self.sub_ip_name.upper())
        files = self.files_xilinx_synth[:]
        if len(files) == 0:
            files.extend(self.files)
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
        synplify_cmd = ""
        files = self.files_xilinx_synth[:]
        if len(files) == 0:
            files.extend(self.files)
        if not self.vhdl:
            for f in files:
                synplify_cmd += "add_file -verilog %s/%s/%s\n" % (abs_path, self.ip_path, f)
        else:
            for f in files:
                synplify_cmd += "add_file -vhdl %s/%s/%s\n" % (abs_path, self.ip_path, f)
        return synplify_cmd
