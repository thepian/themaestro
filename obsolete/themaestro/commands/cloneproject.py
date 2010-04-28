from thepian.cmdline.base import BaseCommand
from optparse import make_option
import sys, os
from subprocess import Popen
from os.path import dirname,abspath,join,split,exists,expanduser,isfile
from thepian.utils import *

class Command(BaseCommand):
    help = 'Clone project from repository making appropriate repositories'
    args = '<repository> <refspec>'

    def handle(self, *names, **options):
        from thepian.conf import structure

        for name in names:
            REMOTE_URL = "ssh://hvendelbo@192.168.9.94/Users/hvendelbo"
            REMOTE_SOURCE = join(REMOTE_URL,"Sites",name,"src")
            REMOTE_RELEASE = join(REMOTE_URL,"Sites",name,"release")
            REMOTE_DESIGN = join(REMOTE_URL,"Sites",name,"design")
            PROJECT_DIR = join(structure.SITES_DIR,name)
            
            makedirs(PROJECT_DIR)
            sp = Popen("git clone %s %s" % (REMOTE_SOURCE,"src"), cwd=PROJECT_DIR, env=None, shell=True)
            sts = os.waitpid(sp.pid, 0)
            sp = Popen("git clone %s %s" % (REMOTE_RELEASE,"release"), cwd=PROJECT_DIR, env=None, shell=True)
            sts = os.waitpid(sp.pid, 0)
            sp = Popen("git clone %s %s" % (REMOTE_DESIGN,"design"), cwd=PROJECT_DIR, env=None, shell=True)
            sts = os.waitpid(sp.pid, 0)
            #TODO if remote exits design, clone it

