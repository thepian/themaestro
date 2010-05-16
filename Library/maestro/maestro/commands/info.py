from __future__ import with_statement
import os
from fs import listdir, makedirs, walk, copy_tree, symlink
from optparse import make_option, OptionParser

from thepian.conf import structure, settings, dependency

class Command(object):
    option_list = ()
    help = 'Info about project containing the current directory'
    args = ''

    def get_version(self):
        return 0.1
        
    def create_parser(self, prog_name, subcommand):
        usage = '%%prog %s [options] %s' % (subcommand, self.args)
        usage = '%s\n\n%s' % (usage, self.help)
        return OptionParser(prog=prog_name,
                            usage=usage,
                            version=self.get_version(),
                            option_list=self.option_list)


    def handle(self, *args, **options):
        print structure
        print settings
