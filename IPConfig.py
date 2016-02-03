#!/usr/bin/env python
# KISS script to load configuration files from IPs

from vsim_defines import *
from SubIPConfig import *

class IPConfig(object):
    def __init__(self, ip_name, ip_dic):
        super(IPConfig, self).__init__()

        self.ip_name = ip_name
        self.sub_ips = {}

        # if the keyword "files" is in the ip_dic dictionary, then there are no sub-IPs
        if "files" in ip_dic.keys():
            self.sub_ips[ip_name] = SubIPConfig(ip_name, ip_name, ip_dic)
        else:
            for k in ip_dic.keys():
                self.sub_ips[k] = SubIPConfig(ip_name, k, ip_dic[k])

    def export_vsim(self, abs_path):
        vsim_script = VSIM_PREAMBLE % (self.ip_name)
        for s in self.sub_ips.keys():
            vsim_script += self.sub_ips[s].export_vsim(abs_path)
        vsim_script += VSIM_POSTAMBLE
        return vsim_script
