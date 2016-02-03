#!/usr/bin/env python
# KISS script to load configuration files from IPs

from vsim_defines import *

class SubIPConfig(object):
    def __init__(self, ip_name, sub_ip_name, sub_ip_dic):
        super(SubIPConfig, self).__init__()

        self.sub_ip_name = sub_ip_name

        try:
            self.incdirs = sub_ip_dic['incdirs']
        except KeyError:
            self.incdirs = []

        try:
            self.files = sub_ip_dic['files']
        except KeyError:
            print "ERROR: failed to find any files associated to ip %s, sub-ip %s." % (ip_name, sub_ip_name)
            sys.exit(1)

    def export_vsim(self, abs_path):
        vlog_cmd  = VSIM_PREAMBLE_SUBIP % (self.sub_ip_name)
        vlog_includes = ""
        for i in self.incdirs:
            vlog_includes += "%s%s/%s" % (VSIM_VLOG_INCDIR_CMD, abs_path, i)
        for f in self.files:
            vlog_cmd += VSIM_VLOG_CMD % (vlog_includes, "%s/%s" % (abs_path, f))
        return vlog_cmd
        