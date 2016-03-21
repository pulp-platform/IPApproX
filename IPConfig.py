#!/usr/bin/env python
# KISS script to load configuration files from IPs

from IPApproX_common  import *
from vsim_defines     import *
from vivado_defines   import *
from synopsys_defines import *
from SubIPConfig      import *

class IPConfig(object):
    def __init__(self, ip_name, ip_dic, ip_path, vsim_dir, domain=None, alternatives=None):
        super(IPConfig, self).__init__()

        self.domain  = domain
        self.alternatives = alternatives
        self.ip_name = ip_name
        self.ip_path = ip_path
        self.vsim_dir = vsim_dir
        self.sub_ips = {}

        # if the keyword "files" is in the ip_dic dictionary, then there are no sub-IPs
        if "files" in ip_dic.keys():
            self.sub_ips[ip_name] = SubIPConfig(ip_name, ip_name, ip_dic, ip_path)
        else:
            for k in ip_dic.keys():
                self.sub_ips[k] = SubIPConfig(ip_name, k, ip_dic[k], ip_path)

    def export_vsim(self, abs_path, more_opts, target_tech='st28fdsoi'):
        vsim_script = VSIM_PREAMBLE % (self.vsim_dir, prepare(self.ip_name), self.ip_path)
        for s in self.sub_ips.keys():
            vsim_script += self.sub_ips[s].export_vsim(abs_path, more_opts, target_tech=target_tech)
        vsim_script += VSIM_POSTAMBLE
        return vsim_script

    def export_synopsys(self, target_tech='st28fdsoi'):
        analyze_script = SYNOPSYS_ANALYZE_PREAMBLE % (self.ip_name)
        for s in self.sub_ips.keys():
            analyze_script += self.sub_ips[s].export_synopsys(self.ip_path, target_tech=target_tech)
        return analyze_script

    def export_vivado(self, abs_path):
        vivado_script = ""
        for s in self.sub_ips.keys():
            vivado_script += self.sub_ips[s].export_vivado(abs_path)
        return vivado_script

    def export_synplify(self, abs_path):
        synplify_script = ""
        for s in self.sub_ips.keys():
            synplify_script += self.sub_ips[s].export_synplify(abs_path)
        return synplify_script

    def generate_vivado_add_files(self):
        l = []
        for s in self.sub_ips.keys():
            if "xilinx" in self.sub_ips[s].targets or "all" in self.sub_ips[s].targets:
                l.append(prepare(s))
        return l

    def generate_vivado_inc_dirs(self):
        l = []
        for s in self.sub_ips.keys():
            if "xilinx" in self.sub_ips[s].targets or "all" in self.sub_ips[s].targets:
                l.extend(self.sub_ips[s].incdirs)
        return l
