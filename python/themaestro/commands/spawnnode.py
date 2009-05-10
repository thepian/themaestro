# Spawning
# node=explicit_cluster

import os,sys, site
from optparse import make_option
from themaestro.commands import DjangoCommand
from thepian.conf import structure

class Command(DjangoCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--noreload', action='store_false', dest='use_reloader', default=True,
            help='Tells Thepian to NOT use the auto-reloader.'),
        #make_option('--cluster', dest='cluster', default='',
        #    help='Specifies which cluster to spawn a node for.'),
        make_option('--daemonize', dest='daemonize', default=False,
            help='Specifies which cluster to spawn a node for.'),
    )
    help = "Starts a lightweight Web server for development."
    args = ''

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False

    def handle(self, *args, **options):
        
        from spawning import run_controller
        sock = None

        if options.restart_args:
            restart_args = simplejson.loads(options.restart_args)
            factory = restart_args['factory']
            factory_args = restart_args['factory_args']

            start_delay = restart_args.get('start_delay')
            if start_delay is not None:
                factory_args['start_delay'] = start_delay
                print "(%s) delaying startup by %s" % (os.getpid(), start_delay)
                time.sleep(start_delay)

            fd = restart_args.get('fd')
            if fd is not None:
                sock = socket.fromfd(restart_args['fd'], socket.AF_INET, socket.SOCK_STREAM)
                ## socket.fromfd doesn't result in a socket object that has the same fd.
                ## The old fd is still open however, so we close it so we don't leak.
                os.close(restart_args['fd'])
        else:
            ## We're starting up for the first time.
            ## Become a process group leader.
            os.setpgrp()
            ## Fork off the thing that watches memory for this process group.
            controller_pid = os.getpid()
            if (options.max_memory or options.max_age) and not os.fork():
                env = environ()
                from spawning import memory_watcher
                basedir, cmdname = os.path.split(memory_watcher.__file__)
                if cmdname.endswith('.pyc'):
                    cmdname = cmdname[:-1]

                os.chdir(basedir)
                command = [
                    'python',
                    cmdname,
                    '--max-age', str(options.max_age),
                    str(controller_pid),
                    str(options.max_memory)]
                os.execve(sys.executable, command, env)

            factory = options.factory
            factory_args = {
                'verbose': options.verbose,
                'host': options.host,
                'port': options.port,
                'num_processes': options.processes,
                'processpool_workers': options.workers,
                'threadpool_workers': options.threads,
                'watch': options.watch,
                'dev': not options.release,
                'deadman_timeout': options.deadman_timeout,
                'access_log_file': options.access_log_file,
                'coverage': options.coverage,
                'args': positional_args,
            }

        run_controller(factory, factory_args, sock)
