from __future__ import with_statement
import fs
from thepian.conf import structure, settings, ensure_target_tree
from optparse import make_option, OptionParser

"""
hosts = Replace all DOMAINS entries in /etc/hosts with fresh ones
"""

class Command(object):
    option_list = (
        make_option('--restart', action='store_true', dest='restart', default=False,
            help='Tells Thepian to restart affected services if configuration changed.'),
    )
    help = 'Enables the directories and configuration needed for the developement/production environment'
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

    def __call__(self, *modulenames, **options):
        try:
            from maestro.config import ensure_areas, install_features

            ensure_target_tree(structure.PROJECT_DIR)
            ensure_areas()
            install_features()

        except Warning, e:
            # print self.style.NOTICE(e.message)
            print e
        except IOError, e:
            # print self.style.ERROR(e.message)
            print e
        except Exception, e:
            print e
            import traceback; traceback.print_exc()
            
        

