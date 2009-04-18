from __future__ import with_statement
import os
from fs import listdir, makedirs, walk, copy_tree, symlink
from optparse import make_option

from thepian.cmdline import BaseCommand, CommandError
from thepian.conf import structure, dependency

class Command(BaseCommand):
    option_list = BaseCommand.option_list + ()
    help = 'Info about project containing the current directory'
    args = ''

    def handle(self, *args, **options):
        print structure
