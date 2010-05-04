import os, sys
from optparse import make_option

class Command(object):
    option_list = ()
    args = "module"
    help = "Runs the tests found in the current directory."

    def __call__(self, *args, **options):
        import py 
        print sys.path, args
        args = ['Library/maestro/mediaserver/sources/jsparser']
        py.test.cmdline.main(args)