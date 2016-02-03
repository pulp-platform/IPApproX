#!/usr/bin/env python
# KISS script to load configuration files from IPs

import yaml
import collections
from IPConfig import *

def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=collections.OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)

class IPDatabase(object):
    def __init__(self):
        super(IPDatabase, self).__init__()
        self.ip_dic = {}

    def import_yaml(self, ip_name, filename):
        with open(filename, "rb") as f:
            ip_dic = ordered_load(f, yaml.SafeLoader)

        try:
            self.ip_dic[ip_name] = IPConfig(ip_name, ip_dic)
        except KeyError:
            print("Skipped IP %s from %s config file as it seems it is already in the IP Config database." % (ip_name, filename))

    def export_vsim(self, abs_path, script_path="./"):
        for i in self.ip_dic.keys():
            filename = "%svcompile_%s.csh" % (script_path, i)
            vcompile_script = self.ip_dic[i].export_vsim(abs_path)
            with open(filename, "wb") as f:
                f.write(vcompile_script)
