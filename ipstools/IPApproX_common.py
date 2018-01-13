#!/usr/bin/env python
#
# IPApproX_common.py
# Francesco Conti <f.conti@unibo.it>
#
# Copyright (C) 2015-2017 ETH Zurich, University of Bologna
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.
#

from __future__ import print_function
import re, os, subprocess, sys, os, stat
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
sys.path.append(os.path.abspath("yaml/lib64/python"))
import yaml
if sys.version_info[0]==2 and sys.version_info[1]>=7:
    from collections import OrderedDict
elif sys.version_info[0]>2:
    from collections import OrderedDict
else:
    from ordereddict import OrderedDict

def prepare(s):
    return re.sub("[^a-zA-Z0-9_]", "_", s)

class tcolors:
    OK      = '\033[92m'
    WARNING = '\033[93m'
    ERROR   = '\033[91m'
    ENDC    = '\033[0m'
    BLUE    = '\033[94m'

def execute(cmd, silent=False):
    with open(os.devnull, "wb") as devnull:
        if silent:
            stdout = devnull
        else:
            stdout = None

        return subprocess.call(cmd.split(), stdout=stdout)

def execute_out(cmd, silent=False):
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    out, err = p.communicate()

    return out

def execute_popen(cmd, silent=False):
    with open(os.devnull, "wb") as devnull:
        if silent:
            return subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=devnull)
        else:
            return subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)

def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)

def load_ips_list(filename, skip_commit=False):
    # get a list of all IPs that we are interested in from ips_list.yml
    with open(filename, "rb") as f:
        ips_list = ordered_load(f, yaml.SafeLoader)
    ips = []
    for i in ips_list.keys():
        if not skip_commit:
            commit = ips_list[i]['commit']
        else:
            commit = None
        try:
            domain = ips_list[i]['domain']
        except KeyError:
            domain = None
        try:
            group = ips_list[i]['group']
        except KeyError:
            group = None
        try:
            path = ips_list[i]['path']
        except KeyError:
            path = i
        name = i.split()[0].split('/')[-1]
        try:
            alternatives = list(set.union(set(ips_list[i]['alternatives']), set([name])))
        except KeyError:
            alternatives = None
        ips.append({'name': name, 'commit': commit, 'group': group, 'path': path, 'domain': domain, 'alternatives': alternatives })
    return ips

def store_ips_list(filename, ips):
    ips_list = {}
    for i in ips:
        if i['alternatives'] != None:
            ips_list[i['path']] = {'commit': i['commit'], 'group': i['group'], 'domain': i['domain'], 'alternatives': i['alternatives']}
        else:
            ips_list[i['path']] = {'commit': i['commit'], 'group': i['group'], 'domain': i['domain']}
    with open(filename, "wb") as f:
        f.write(IPS_LIST_PREAMBLE)
        f.write(yaml.dump(ips_list))

def get_ips_list_yml(server="git@iis-git.ee.ethz.ch", group='pulp-open', name='mr-wolf.git', commit='master'):
    with open(os.devnull, "wb") as devnull:
        cmd = "git archive --remote=%s:%s/%s %s ips_list.yml" % (server, group, name, commit)
        git_archive = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=devnull)
        cmd = "tar -xO"
        try:
            ips_list_yml = subprocess.check_output(cmd.split(), stdin=git_archive.stdout, stderr=devnull)
            git_archive.wait()
        except subprocess.CalledProcessError:
            ips_list_yml = None
    # ips_list_yml, err = execute_popen("git archive --remote=%s:%s/%s %s ips_list.yml" % (server, group, name, commit), silent=True).communicate()
    return ips_list_yml

def load_ips_list_from_server(server="git@iis-git.ee.ethz.ch", group='pulp-open', name='mr-wolf.git', commit='master', skip_commit=False):
    ips_list_yml = get_ips_list_yml(server, group, name, commit)
    if ips_list_yml is None:
        return []
    f = StringIO(ips_list_yml)
    ips_list = ordered_load(f, yaml.SafeLoader)
    ips = []
    for i in ips_list.keys():
        if not skip_commit:
            commit = ips_list[i]['commit']
        else:
            commit = None
        try:
            domain = ips_list[i]['domain']
        except KeyError:
            domain = None
        try:
            group = ips_list[i]['group']
        except KeyError:
            group = None
        try:
            path = ips_list[i]['path']
        except KeyError:
            path = i
        name = i.split()[0].split('/')[-1]
        try:
            alternatives = list(set.union(set(ips_list[i]['alternatives']), set([name])))
        except KeyError:
            alternatives = None
        ips.append({'name': name, 'commit': commit, 'group': group, 'path': path, 'domain': domain, 'alternatives': alternatives })
    return ips
