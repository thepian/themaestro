# Spawning
# node=explicit_cluster

import os,sys, site
from optparse import make_option
from thepian.cmdline.base import NoArgsCommand
from thepian.conf import import_structure

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--noreload', action='store_false', dest='use_reloader', default=True,
            help='Tells Thepian to NOT use the auto-reloader.'),
        make_option('--cluster', dest='cluster', default='',
            help='Specifies which cluster to spawn a node for.'),
        make_option('--daemonize', dest='daemonize', default=False,
            help='Specifies which cluster to spawn a node for.'),
    )
    help = "Starts a lightweight Web server for development."
    args = ''

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False

    def handle_noargs(self, addrport='', **options):
        structure = import_structure(os.getcwd()) #TODO support release
        site.addsitedir(structure.PYTHON_DIR)
        if structure.DEVELOPING:
            site.addsitedir(structure.LIB_DIR)
        try:
            from conf import settings
        except ImportError:
            sys.stderr.write("""Error: Can't find the file 'settings.py' in the conf directory of %r. It appears you've customized things. 
    You'll have to run django-admin.py, passing it your settings module.
    (If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n"""  % __file__)
            sys.exit(1)

        import django
        from django.core.management import setup_environ
        setup_environ(settings)
        
        from django.core.servers.basehttp import run, AdminMediaHandler, WSGIServerException
        from django.core.handlers.wsgi import WSGIHandler

        if not addrport:
            addr = ''
            port = '8000'
        else:
            try:
                addr, port = addrport.split(':')
            except ValueError:
                addr, port = '', addrport
        if not addr:
            addr = '127.0.0.1'

        if not port.isdigit():
            raise CommandError("%r is not a valid port number." % port)

        use_reloader = options.get('use_reloader', True)
        admin_media_path = options.get('admin_media_path', '')
        shutdown_message = options.get('shutdown_message', '')
        quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'

        def inner_run():
            from django.conf import settings
            print "Validating models..."
            self.validate(display_num_errors=True)
            print "\nDjango version %s, using settings %r" % (django.get_version(), settings.SETTINGS_MODULE)
            print "Development server is running at http://%s:%s/" % (addr, port)
            print "Quit the server with %s." % quit_command
            try:
                path = admin_media_path or django.__path__[0] + '/contrib/admin/media'
                handler = AdminMediaHandler(WSGIHandler(), path)
                run(addr, int(port), handler)
            except WSGIServerException, e:
                # Use helpful error messages instead of ugly tracebacks.
                ERRORS = {
                    13: "You don't have permission to access that port.",
                    98: "That port is already in use.",
                    99: "That IP address can't be assigned-to.",
                }
                try:
                    error_text = ERRORS[e.args[0].args[0]]
                except (AttributeError, KeyError):
                    error_text = str(e)
                sys.stderr.write(self.style.ERROR("Error: %s" % error_text) + '\n')
                # Need to use an OS exit because sys.exit doesn't work in a thread
                os._exit(1)
            except KeyboardInterrupt:
                if shutdown_message:
                    print shutdown_message
                sys.exit(0)
        if use_reloader:
            from django.utils import autoreload
            autoreload.main(inner_run)
        else:
            inner_run()
