import os, sys
from optparse import make_option

class Command(object):
    option_list = ()
    args = "module"
    help = "Runs the tests found in the current directory."

    def __call__(self, *args, **options):
        import py 
        if not args:
            args = [
                'Library/maestro/thepian/conf',
                'Library/maestro/mediaserver',
                'Library/maestro/ecmatic']
        py.test.cmdline.main(args)