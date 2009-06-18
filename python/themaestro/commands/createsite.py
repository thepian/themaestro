from __future__ import with_statement
import sys,os,re,fs
from optparse import make_option
from subprocess import Popen
from os.path import dirname,abspath,join,split,exists,expanduser,isfile, isdir
from random import choice

from thepian.cmdline.base import BaseCommand
from thepian.utils import *
from thepian.conf import create_site_structure
from themaestro.config import copy_template
from themaestro.conf import templates

EASYINSTALL_NAMES = ['zc.buildout','netifaces','pytz-2008e','feedparser-4.1','markdown-1.7',
                'simplejson-1.9.2', 'textile-2.0.11','vobject-0.7.1','python_dateutil-1.4.1',
                'python_openid-2.2.1','python_magic-0.1']
                
class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--verbosity', action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),
        #make_option('--extended', action='store_true', dest='extended', default=False,
        #    help='Include source for C++ and Java'),
        #make_option('--django', action='store_true', dest='django', default=False,
        #    help='Include Django applications')
    )
    help = 'Add new project/site to Sites folder. To set up a project from the thepian repository, use the clone command. Site folder is determined by thepian.conf'
    args = 'name'
    
    def handle(self, *projects, **options):
        
        if len(projects) == 0:
            self.style.ERROR("You must specify project name")
            return

        if isdir("/Sites/skeleton"):
            skeleton_path = "/Sites/skeleton"
        else:
            skeleton_path = "git://github.com/thepian/skeleton"
        project_path = join("/Sites",projects[0])
        sp = Popen("git clone %s %s" % (skeleton_path,project_path),cwd="/Sites",env=None,shell=True)
        sts = os.waitpid(sp.pid, 0)

        structure = create_site_structure(projects[0])
        vars = { 'projectname':projects[0] }

        with open(join(structure.SOURCE_DIR,'.gitignore'),"w") as g:
            g.write(templates.SINGLE_IGNORE % vars)
            g.flush()
        with open(join(structure.SOURCE_DIR,'.git','config'), "w") as c:
            c.write(templates.WORK_SINGLE_CONFIG % vars)
            c.flush()
            
        #copy_template(self.style,'single',projects[0],structure.SOURCE_DIR)

        # Create a random AFFINITY_SECRET hash, and put it in the main structure.
        main_structure_file = join(structure.CONF_DIR, 'structure.py')
        structure_contents = open(main_structure_file, 'r').read()
        with open(main_structure_file, 'w') as fp:
            affinity_secret_key = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
            structure_contents = re.sub(r"(?<=AFFINITY_SECRET = ')'", affinity_secret_key + "'", structure_contents)
            fp.write(structure_contents)

        # Create a random SECRET_KEY hash, and put it in the main settings.
        main_settings_file = join(structure.CONF_DIR, 'settings.py')
        settings_contents = open(main_settings_file, 'r').read()
        with open(main_settings_file, 'w') as fp:
            secret_key = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
            settings_contents = re.sub(r"(?<=SECRET_KEY = ')'", secret_key + "'", settings_contents)
            fp.write(settings_contents)

        sp = Popen("git add .",cwd=structure.SOURCE_DIR,env=None,shell=True)
        sts = os.waitpid(sp.pid,0)

        return
        
        
        
        sp = Popen("git init",cwd=structure.SOURCE_DIR,env=None,shell=True)
        sts = os.waitpid(sp.pid, 0)
            
        if exists(join(structure.SOURCE_DIR,"bin","easy_install")):
            for name in EASYINSTALL_NAMES:
                sp = Popen("bin/easy_install %s" % name,cwd=structure.SOURCE_DIR,env=None,shell=True)
                sts = os.waitpid(sp.pid,0)

        if exists(join(structure.SOURCE_DIR,"bin","buildout")):
            sp = Popen("bin/buildout",cwd=structure.SOURCE_DIR,env=None,shell=True)
            sts = os.waitpid(sp.pid,0)

        #TODO make_executable(bin/activate bin/thepian)

        #sp = Popen("git commit -a --message='Basic Thepian Config'",cwd=structure.SOURCE_DIR,env=None,shell=True)
        #sts = os.waitpid(sp.pid,0)
        
        print 'use commands updateconf and enablesite to complete the project setup'


#$ virtualenv --no-site-packages newproject
#$ cd newproject
#$ bin/easy_install zc.buildout
#$ bin/buildout init