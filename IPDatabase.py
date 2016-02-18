#!/usr/bin/env python
# KISS script to load configuration files from IPs

# YAML workaround
import sys,os
sys.path.append(os.path.abspath("yaml/lib64/python"))
import yaml
import collections
from IPConfig import *
from IPApproX_common import *
from vivado_defines import *
from synopsys_defines import *

IP_DIR = "fe/ips"

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
    # get a list of all IPs that we are interested in from ips_list.yml
    with open(filename, "rb") as f:
        ips_list = ordered_load(f, yaml.SafeLoader)
    ips = []
    for i in ips_list.keys():
        commit = ips_list[i]['commit']
        domain = ips_list[i]['domain']
        path = i
        name = i.split()[0].split('/')[-1]
        ips.append({'name': name, 'commit': commit, 'path': path, 'domain': domain })
    return ips

class IPDatabase(object):
    def __init__(self, ips_list_path=".", skip_scripts=False):
        super(IPDatabase, self).__init__()
        self.ip_dic = {}
        ips_list_yml = "%s/ips_list.yml" % (ips_list_path)
        self.ip_list = load_ips_list(ips_list_yml)
        if not skip_scripts:
            for ip in self.ip_list:
                ip_full_name = ip['name']
                ip_full_path = "%s/%s/%s/src_files.yml" % (ips_list_path, IP_DIR, ip['path'])
                self.import_yaml(ip_full_name, ip_full_path, ip['path'])

    def import_yaml(self, ip_name, filename, ip_path):
        if not os.path.exists(os.path.dirname(filename)):
            print(tcolors.ERROR + "ERROR: ip '%s' does not exist." % ip_name + tcolors.ENDC)
            sys.exit(1)
        try:
            with open(filename, "rb") as f:
                ip_dic = ordered_load(f, yaml.SafeLoader)
        except IOError:
            print(tcolors.WARNING + "WARNING: Skipped ip '%s' as it has no src_files.yml file." % ip_name + tcolors.ENDC)
            return

        try:
            self.ip_dic[ip_name] = IPConfig(ip_name, ip_dic, ip_path)
        except KeyError:
            print(tcolors.WARNING + "WARNING: Skipped ip '%s' with %s config file as it seems it is already in the ip database." % (ip_name, filename) + tcolors.ENDC)

    def diff_ips(self):
        prepend = "  "
        ips = self.ip_list
        cwd = os.getcwd()
        for ip in ips:
            try:
                os.chdir("./fe/ips/%s" % ip['path'])
                output, err = execute_popen("git diff --name-only").communicate()
                unstaged_out = ""
                if output.split("\n")[0] != "":
                    for line in output.split("\n"):
                        l = line.split()
                        try:
                            unstaged_out += "%s%s\n" % (prepend, l[0])
                        except IndexError:
                            break
                output, err = execute_popen("git diff --cached --name-only").communicate()
                staged_out = ""
                if output.split("\n")[0] != "":
                    for line in output.split("\n"):
                        l = line.split()
                        try:
                            staged_out += "%s%s\n" % (prepend, l[0])
                        except IndexError:
                            break
                os.chdir(cwd)
                if unstaged_out != "":
                    print "Changes not staged for commit in ip " + tcolors.WARNING + "'%s'" % ip['name'] + tcolors.ENDC + "."
                    print unstaged_out
                if staged_out != "":
                    print "Changes staged for commit in ip " + tcolors.WARNING + "'%s'" % ip['name'] + tcolors.ENDC + ".\nUse " + tcolors.BLUE + "git reset HEAD" + tcolors.ENDC + " in the ip directory to unstage."
                    print staged_out
            except OSError:
                print "WARNING: Skipping ip " + tcolors.WARNING + "'%s'" % ip['name'] + tcolors.ENDC + " as it doesn't exist."

    def update_ips(self):
        errors = []
        ips = self.ip_list
        git = "git"
        ip_dir = "fe/ips/"
        server = "git@iis-git.ee.ethz.ch:pulp-project"
        # make sure we are in the correct directory to start
        os.chdir(ip_dir)
        cwd = os.getcwd()

        for ip in ips:
            os.chdir(cwd)
            # check if directory already exists, this hints to the fact that we probably already cloned it
            if os.path.isdir("./%s" % ip['path']):
                os.chdir("./%s" % ip['path'])

                # now check if the directory is a git directory
                if not os.path.isdir(".git"):
                    print tcolors.ERROR + "ERROR: Found a normal directory instead of a git directory at %s. You may have to delete this folder to make this script work again" % os.getcwd() + tcolors.ENDC
                    errors.append("%s - %s: Not a git directory" % (ip['name'], ip['path']));
                    continue

                print tcolors.OK + "\nUpdating ip '%s'..." % ip['name'] + tcolors.ENDC

                # fetch everything first so that all commits are available later
                ret = execute("%s fetch" % (git))
                if ret != 0:
                    print tcolors.ERROR + "ERROR: could not fetch ip '%s'." % (ip['name']) + tcolors.ENDC
                    errors.append("%s - Could not fetch" % (ip['name']));
                    continue

                # make sure we have the correct branch/tag for the pull
                ret = execute("%s checkout %s" % (git, ip['commit']))
                if ret != 0:
                    print tcolors.ERROR + "ERROR: could not checkout ip '%s' at %s." % (ip['name'], ip['commit']) + tcolors.ENDC
                    errors.append("%s - Could not checkout commit %s" % (ip['name'], ip['commit']));
                    continue

                # check if we are in detached HEAD mode
                stdout = execute_out("%s status" % git)

                if not ("HEAD detached" in stdout):
                    # only do the pull if we are not in detached head mode
                    ret = execute("%s pull --ff-only" % git)
                    if ret != 0:
                        print tcolors.ERROR + "ERROR: could not update ip '%s'" % ip['name'] + tcolors.ENDC
                        errors.append("%s - Could not update" % (ip['name']));
                        continue

            # Not yet cloned, so we have to do that first
            else:
                os.chdir("./")

                print tcolors.OK + "\nCloning ip '%s'..." % ip['name'] + tcolors.ENDC

                ret = execute("%s clone %s/%s.git %s" % (git, server, ip['name'], ip['path']))
                if ret != 0:
                    print tcolors.ERROR + "ERROR: could not clone, you probably have to remove the '%s' directory." % ip['name'] + tcolors.ENDC
                    errors.append("%s - Could not clone" % (ip['name']));
                    continue
                os.chdir("./%s" % ip['path'])
                ret = execute("%s checkout %s" % (git, ip['commit']))
                if ret != 0:
                    print tcolors.ERROR + "ERROR: could not checkout ip '%s' at %s." % (ip['name'], ip['commit']) + tcolors.ENDC
                    errors.append("%s - Could not checkout commit %s" % (ip['name'], ip['commit']));
                    continue
        os.chdir(cwd)
        print '\n\n'
        print tcolors.WARNING + "SUMMARY" + tcolors.ENDC
        if len(errors) == 0:
            print tcolors.OK + "IPs updated successfully!" + tcolors.ENDC
        else:
            for error in errors:
                print tcolors.ERROR + '    %s' % (error) + tcolors.ENDC
            print
            print tcolors.ERROR + "ERRORS during IP update!" + tcolors.ENDC
            sys.exit(1)

    def export_vsim(self, abs_path="${IP_PATH}", script_path="./", more_opts="", target_tech='st28fdsoi'):
        for i in self.ip_dic.keys():
            filename = "%svcompile_%s.csh" % (script_path, i)
            vcompile_script = self.ip_dic[i].export_vsim(abs_path, more_opts, target_tech=target_tech)
            with open(filename, "wb") as f:
                f.write(vcompile_script)

    def export_synopsys(self, script_path=".", target_tech='st28fdsoi'):
        for i in self.ip_dic.keys():
            filename = "%s/analyze_%s.tcl" % (script_path, i)
            analyze_script = self.ip_dic[i].export_synopsys(target_tech=target_tech)
            with open(filename, "wb") as f:
                f.write(analyze_script)

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

    def generate_vivado_add_files(self, filename):
        l = []
        vivado_add_files_cmd = ""
        for i in self.ip_dic.keys():
            l.extend(self.ip_dic[i].generate_vivado_add_files())
        for el in l:
            vivado_add_files_cmd += VIVADO_ADD_FILES_CMD % el.upper()
        with open(filename, "wb") as f:
            f.write(vivado_add_files_cmd)

    def generate_vivado_inc_dirs(self, filename):
        l = []
        vivado_inc_dirs = VIVADO_INC_DIRS_PREAMBLE
        for i in self.ip_dic.keys():
            incdirs = []
            path = self.ip_dic[i].ip_path
            for j in self.ip_dic[i].generate_vivado_inc_dirs():
                incdirs.append("%s/%s" % (path, j))
            l.extend(incdirs)
        for el in l:
            vivado_inc_dirs += VIVADO_INC_DIRS_CMD % el
        vivado_inc_dirs += VIVADO_INC_DIRS_POSTAMBLE
        with open(filename, "wb") as f:
            f.write(vivado_inc_dirs)
