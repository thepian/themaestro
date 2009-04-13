from fs import makedirs
from theapps.utils.djangoextras import DjangoCommand
from thepian.conf import structure
from optparse import make_option

class Command(DjangoCommand):
    option_list = DjangoCommand.option_list + (
        make_option('--daemonize', action='store_true', dest='daemonize', default=False,
            help='Tells Thepian to NOT run the command in as a separate process'),
    )
    help = "Runs this project as a FastCGI application. Requires flup."
    args = '[various KEY=val options, use `runfcgi help` for help]'

    def handle(self, *args, **options):
        from django.conf import settings
        from django.utils import translation
        # Activate the current language, because it won't get activated later.
        try:
            translation.activate(settings.LANGUAGE_CODE)
        except AttributeError:
            pass
        runfastcgi(**options)
        
    def usage(self, subcommand):
        from django.core.servers.fastcgi import FASTCGI_HELP
        return FASTCGI_HELP


FASTCGI_OPTIONS = {
    'protocol': 'fcgi',
    'host': '127.0.0.1',
    'port': None,
    'socket': None,
    'method': 'fork',
    'daemonize': None,
    'workdir': '/',
    'pidfile': None,
    'maxspare': 5,
    'minspare': 2,
    'maxchildren': 50,
    'maxrequests': 0,
    'outlog': None,
    'errlog': None,
    'umask': None,
}

def runfastcgi(**kwargs):
    options = FASTCGI_OPTIONS.copy()
    for n in options:
        n2 = 'upstream_%s' % n
        if n2 in structure.CLUSTER:
            options[n] = structure.CLUSTER[n2]
            print n, options[n], 'copied'
    
    options.update(kwargs)
    if options['socket']:
        options['port'] = None
        options['host'] = None
    if "help" in options:
        return fastcgi_help()

    try:
        import flup
    except ImportError, e:
        print >> sys.stderr, "ERROR: %s" % e
        print >> sys.stderr, "  Unable to load the flup package.  In order to run django"
        print >> sys.stderr, "  as a FastCGI application, you will need to get flup from"
        print >> sys.stderr, "  http://www.saddi.com/software/flup/   If you've already"
        print >> sys.stderr, "  installed flup, then make sure you have it in your PYTHONPATH."
        return False

    if structure.INCOMPLETE:
        print >> sys.stderr, "ERROR: %s" % structure.INCOMPLETE
        print >> sys.stderr, "Cannot run node without a complete support structure."
        return False
    
    p = options['protocol'] == "fastcgi" and "fcgi" or options['protocol']
    flup_module = 'server.' + p

    if options['method'] in ('prefork', 'fork'):
        wsgi_opts = {
            'maxSpare': int(options["maxspare"]),
            'minSpare': int(options["minspare"]),
            'maxChildren': int(options["maxchildren"]),
            'maxRequests': int(options["maxrequests"]), 
        }
        flup_module += '_fork'
    elif options['method'] in ('thread', 'threaded'):
        wsgi_opts = {
            'maxSpare': int(options["maxspare"]),
            'minSpare': int(options["minspare"]),
            'maxThreads': int(options["maxchildren"]),
        }
    else:
        return fastcgi_help("ERROR: Implementation must be one of prefork or thread.")

    #wsgi_opts['debug'] = False # Turn off flup tracebacks

    try:
        WSGIServer = getattr(__import__('flup.' + flup_module, '', '', flup_module), 'WSGIServer')
    except:
        print "Can't import flup." + flup_module
        return False

    # Prep up and go
    from django.core.handlers.wsgi import WSGIHandler

    if options["host"] and options["port"] and not options["socket"]:
        wsgi_opts['bindAddress'] = (options["host"], int(options["port"]))
    elif options["socket"] and not options["host"] and not options["port"]:
        wsgi_opts['bindAddress'] = options["socket"]
    elif not options["socket"] and not options["host"] and not options["port"]:
        wsgi_opts['bindAddress'] = None
    else:
        return fastcgi_help("Invalid combination of host, port, socket.")

    if options["daemonize"] is None:
        # Default to daemonizing if we're running on a socket/named pipe.
        daemonize = (wsgi_opts['bindAddress'] is not None)

    daemon_kwargs = {}
    if options['outlog']:
        daemon_kwargs['out_log'] = options['outlog']
    if options['errlog']:
        daemon_kwargs['err_log'] = options['errlog']
    if options['umask']:
        daemon_kwargs['umask'] = int(options['umask'])

    if options['daemonize']:
        from django.utils.daemonize import become_daemon
        become_daemon(our_home_dir=options["workdir"], **daemon_kwargs)

    if not options["pidfile"]:
        from os.path import join
        options["pidfile"] = join(structure.PID_DIR,"node.pid")
    if options["pidfile"]:
        import os
        fp = open(options["pidfile"], "w")
        fp.write("%d\n" % os.getpid())
        fp.close()

    WSGIServer(WSGIHandler(), **wsgi_opts).run()

