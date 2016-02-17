#!/usr/bin/env python
# KISS script to load configuration files from IPs

# YAML workaround
import sys,os
sys.path.append(os.path.abspath("yaml/lib64/python"))
import yaml
import collections
from IPConfig import *
from vivado_defines import *
import re

IP_DIR = "fe/ips"

def prepare(s):
    return re.sub("[^a-zA-Z0-9_]", "_", s)

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

def load_ips_list(filename):
    # get a list of all IPs that we are interested in from ips_list.txt
    with open(filename, "rb") as f:
        ips_list = f.readlines()
    ips = []
    for ips_el in ips_list:
        if ips_el[0] == "#":
            continue
        try:
            splits = ips_el.split()
            path   = splits[0]
            commit = splits[1]
            path_split = splits[0].split('/')
            name = path_split[-1]
            ips.append({'name': name, 'commit': commit, 'path': path })
        except IndexError:
            continue
    return ips

class IPDatabase(object):
    def __init__(self, ips_list_path="."):
        super(IPDatabase, self).__init__()
        self.ip_dic = {}
        ips_list_txt = "%s/ips_list.txt" % (ips_list_path)
        self.ip_list = load_ips_list(ips_list_txt)
        for ip in self.ip_list:
            # if ip['path'] == "":
            #     ip_full_name = ip['name']
            # else:
            #     ip_full_name = "%s_%s" % (ip['path'], ip['name'])
            ip_full_name = ip['name']
            ip_full_path = "%s/%s/%s/src_files.yml" % (ips_list_path, IP_DIR, ip['path'])
            self.import_yaml(ip_full_name, ip_full_path, ip['path'])

    def import_yaml(self, ip_name, filename, ip_path):
        try:
            with open(filename, "rb") as f:
                ip_dic = ordered_load(f, yaml.SafeLoader)
        except IOError:
            print("WARNING: Skipped ip '%s' as it has no src_files.yml file." % (ip_name))
            return

        try:
            self.ip_dic[ip_name] = IPConfig(ip_name, ip_dic, ip_path)
        except KeyError:
            print("Skipped ip '%s' with %s config file as it seems it is already in the ip database." % (ip_name, filename))

    def export_vsim(self, abs_path="${IP_PATH}", script_path="./", more_opts="", target_tech='st28fdsoi'):
        for i in self.ip_dic.keys():
            filename = "%svcompile_%s.csh" % (script_path, i)
            vcompile_script = self.ip_dic[i].export_vsim(abs_path, more_opts, target_tech=target_tech)
            with open(filename, "wb") as f:
                f.write(vcompile_script)

    def export_vivado(self, abs_path="$IPS", script_path="./src_files.tcl", more_opts=""):
        filename = "%s" % (script_path)
        vivado_script = VIVADO_PREAMBLE
        for i in self.ip_dic.keys():
            vivado_script += self.ip_dic[i].export_vivado(abs_path, more_opts)
        with open(filename, "wb") as f:
            f.write(vivado_script)

    def export_synplify(self, abs_path="$IPS", script_path="./src_files_synplify.tcl", more_opts=""):
        filename = "%s" % (script_path)
        synplify_script = ""
        for i in self.ip_dic.keys():
            synplify_script += self.ip_dic[i].export_synplify(abs_path, more_opts)
        with open(filename, "wb") as f:
            f.write(synplify_script)

    def generate_vsim_tcl(self, filename):
        l = []
        for i in self.ip_dic.keys():
            l.append(i)
        vsim_tcl = VSIM_TCL_PREAMBLE
        for el in l:
            vsim_tcl += VSIM_TCL_CMD % prepare(el)
        vsim_tcl += VSIM_TCL_POSTAMBLE
        with open(filename, "wb") as f:
            f.write(vsim_tcl)

    def generate_vcompile_libs_csh(self, filename):
        l = []
        for i in self.ip_dic.keys():
            l.append(i)
        vcompile_libs = VCOMPILE_LIBS_PREAMBLE
        for el in l:
            vcompile_libs += VCOMPILE_LIBS_CMD % el
        with open(filename, "wb") as f:
            f.write(vcompile_libs)
