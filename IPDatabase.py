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
from ips_defines import *
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

def store_ips_list(filename, ips):
    ips_list = {}
    for i in ips:
        ips_list[i['path']] = {'commit': i['commit'], 'domain': i['domain']}
    with open(filename, "wb") as f:
        f.write(IPS_LIST_PREAMBLE)
        f.write(yaml.dump(ips_list))

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
                self.import_yaml(ip_full_name, ip_full_path, ip['path'], domain=ip['domain'])
            sub_ip_check_list = []
            for i in self.ip_dic.keys():
                sub_ip_check_list.extend(self.ip_dic[i].sub_ips.keys())
            if len(set(sub_ip_check_list)) != len(sub_ip_check_list):
                print(tcolors.WARNING + "WARNING: two sub-IPs have the same name. This can cause trouble!" + tcolors.ENDC)

    def import_yaml(self, ip_name, filename, ip_path, domain=None):
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
            self.ip_dic[ip_name] = IPConfig(ip_name, ip_dic, ip_path, domain=domain)
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
        owd = os.getcwd()
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
        os.chdir(owd)

    def delete_tag_ips(self, tag_name):
        cwd = os.getcwd()
        ips = self.ip_list
        new_ips = []
        for ip in ips:
            os.chdir("./fe/ips/%s" % ip['path'])
            ret = execute("git tag -d %s" % tag_name)
            os.chdir(cwd)

    def push_tag_ips(self):
        cwd = os.getcwd()
        ips = self.ip_list
        new_ips = []
        for ip in ips:
            os.chdir("./fe/ips/%s" % ip['path'])
            newest_tag = execute_popen("git describe --tags --abbrev=0", silent=True).communicate()
            try:
                newest_tag = newest_tag[0].split()
                newest_tag = newest_tag[0]
            except IndexError:
                pass
            ret = execute("git push origin tags/%s" % newest_tag)
            os.chdir(cwd)

    def tag_ips(self, tag_name, changes_severity='warning'):
        cwd = os.getcwd()
        ips = self.ip_list
        new_ips = []
        for ip in ips:
            os.chdir("./fe/ips/%s" % ip['path'])
            newest_tag, err = execute_popen("git describe --tags --abbrev=0", silent=True).communicate()
            unstaged_changes, err = execute_popen("git diff --name-only").communicate()
            staged_changes, err = execute_popen("git diff --name-only").communicate()
            if staged_changes.split("\n")[0] != "":
                if changes_severity == 'warning':
                    print tcolors.WARNING + "WARNING: skipping ip '%s' as it has changes staged for commit." % ip['name'] + tcolors.ENDC + "\nSolve, commit and " + tcolors.BLUE + "git tag %s" % tag_name + tcolors.ENDC + " manually."
                    os.chdir(cwd)
                    continue
                else:
                    print tcolors.ERROR + "ERROR: ip '%s' has changes staged for commit." % ip['name'] + tcolors.ENDC + "\nSolve and commit before trying to auto-tag."
                    sys.exit(1)
            if unstaged_changes.split("\n")[0] != "":
                if changes_severity == 'warning':
                    print tcolors.WARNING + "WARNING: skipping ip '%s' as it has unstaged changes." % ip['name'] + tcolors.ENDC + "\nSolve, commit and " + tcolors.BLUE + "git tag %s" % tag_name + tcolors.ENDC + " manually."
                    os.chdir(cwd)
                    continue
                else:
                    print tcolors.ERROR + "ERROR: ip '%s' has unstaged changes." % ip['name'] + tcolors.ENDC + "\nSolve and commit before trying to auto-tag."
                    sys.exit(1)
            if newest_tag != "":
                output, err = execute_popen("git diff --name-only tags/%s" % newest_tag).communicate()
            else:
                output = ""
            if output.split("\n")[0] != "" or newest_tag=="":
                ret = execute("git tag %s" % tag_name)
                if ret != 0:
                    print tcolors.WARNING + "WARNING: could not tag ip '%s', probably the tag already exists." % (ip['name']) + tcolors.ENDC
                else:
                    print "Tagged ip " + tcolors.WARNING + "'%s'" % ip['name'] + tcolors.ENDC + " with tag %s." % tag_name
                newest_tag = tag_name
            try:
                newest_tag = newest_tag.split()[0]
            except IndexError:
                pass
            new_ips.append({'name': ip['name'], 'path': ip['path'], 'domain': ip['domain'], 'commit': "tags/%s" % newest_tag})
            os.chdir(cwd)

        store_ips_list("new_ips_list.yml", new_ips)

    def export_vsim(self, abs_path="${IP_PATH}", script_path="./", more_opts="", target_tech='st28fdsoi'):
        for i in self.ip_dic.keys():
            filename = "%s/vcompile_%s.csh" % (script_path, i)
            vcompile_script = self.ip_dic[i].export_vsim(abs_path, more_opts, target_tech=target_tech)
            with open(filename, "wb") as f:
                f.write(vcompile_script)

    def export_synopsys(self, script_path=".", target_tech='st28fdsoi', domain=None):
        for i in self.ip_dic.keys():
            if domain==None or domain in self.ip_dic[i].domain:
                filename = "%s/analyze_%s.tcl" % (script_path, i)
                analyze_script = self.ip_dic[i].export_synopsys(target_tech=target_tech)
                with open(filename, "wb") as f:
                    f.write(analyze_script)

    def export_vivado(self, abs_path="$IPS", script_path="./src_files.tcl", domain=None):
        filename = "%s" % (script_path)
        vivado_script = VIVADO_PREAMBLE
        for i in self.ip_dic.keys():
            if domain==None or domain in self.ip_dic[i].domain:
                vivado_script += self.ip_dic[i].export_vivado(abs_path)
        with open(filename, "wb") as f:
            f.write(vivado_script)

    def export_synplify(self, abs_path="$IPS", script_path="./src_files_synplify.tcl"):
        filename = "%s" % (script_path)
        synplify_script = ""
        for i in self.ip_dic.keys():
            synplify_script += self.ip_dic[i].export_synplify(abs_path)
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

    def generate_vivado_add_files(self, filename, domain=None):
        l = []
        vivado_add_files_cmd = ""
        for i in self.ip_dic.keys():
            if domain==None or domain in self.ip_dic[i].domain:
                l.extend(self.ip_dic[i].generate_vivado_add_files())
        for el in l:
            vivado_add_files_cmd += VIVADO_ADD_FILES_CMD % el.upper()
        with open(filename, "wb") as f:
            f.write(vivado_add_files_cmd)

    def generate_vivado_inc_dirs(self, filename, domain=None):
        l = []
        vivado_inc_dirs = VIVADO_INC_DIRS_PREAMBLE
        for i in self.ip_dic.keys():
            if domain==None or domain in self.ip_dic[i].domain:
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
