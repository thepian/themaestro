"""
Fundamental Command definitions
Taken from the Django core
"""
from __future__ import with_statement
import os, re
import sys, traceback
import select, socket
from optparse import make_option, OptionParser

from thepian.cmdline.color import color_style
from thepian.conf import handle_default_options
from thepian.utils import *
from os.path import join, abspath, expanduser, exists, isdir, dirname

class ImproperlyConfigured(Exception):
    pass
    
class CommandError(Exception):
    pass

def determine_settings_module(argv):
    """Parse command line options to determine what settings module to use.
    In the absense of an option use environment variable MAESTRO_SETTINGS_MODULE, or guess based
    on machine recognition 
    """
    # Preprocess options to extract --settings and --pythonpath.
    # These options could affect the commands that are available, so they
    # must be processed early.
    import thepian
    parser = LaxOptionParser(version=thepian.get_version(), option_list=BaseCommand.option_list) #TODO should the option_list be a param?
    try:
        options, args = parser.parse_args(argv)
        handle_default_options(options)
    except:
        if options.traceback:
            import traceback
            print >>sys.stderr, 'couldn\'t handle default options failed'
            traceback.print_exc()
    from thepian.conf import structure
    if not '%s_SETTINGS_MODULE' % structure.COMMAND_VARIABLE_PREFIX in os.environ: 
        os.environ['%s_SETTINGS_MODULE' % structure.COMMAND_VARIABLE_PREFIX] = 'development' #TODO development vs production
    return os.environ['%s_SETTINGS_MODULE' % structure.COMMAND_VARIABLE_PREFIX]

    
class BaseCommand(object):
    # Metadata about this command.
    option_list = (
        make_option('--cluster', dest="cluster", help='The name of the active cluster'),
        make_option('--settings',
            help='The Python path to a settings module, e.g. "myproject.settings.main". If this isn\'t provided, the MAESTRO_SETTINGS_MODULE environment variable will be used.'),
        make_option('--pythonpath',
            help='A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".'),
        make_option('--traceback', action='store_true',
            help='Print traceback on exception'),
    )
    help = ''
    args = ''

    def __init__(self):
        self.style = color_style()

    def __call__(self, *args, **options):
        try:
            if len(args) and len(self.args)==0:
                raise CommandError("Command doesn't accept any arguments")
            if len(args)==0 and len(self.args) and not re.compile('\[.+\]').match(self.args):
                raise CommandError("Command requires arguments (%s)" % self.args)
            output = self.handle(*args, **options)
            if output:
                print output
        except CommandError, e:
            sys.stderr.write(self.style.ERROR(str('Error: %s\n' % e)))
            sys.exit(1)

    def handle(self, *args, **options):
        raise NotImplementedError()
        
import os
from os.path import exists, join, split, dirname

class ThepianCommand(BaseCommand):
    
    _current_base = None
    
    def get_current_base(self):
        if self._current_base: return self._current_base
        
        d = os.getcwd()
        while len(d) > 0:
            if exists(join(d,'.git')):
                lead,end = split(d)
                if end in ['src','release']:
                    self._current_base = (d,end)
                    return d,end
                else:
                    raise Exception, "Directory structure unknown %s" % d
            d = dirname(d)
        raise Exception, "Command must be used from within a sorce or release repository"
    
    current_base = property(get_current_base)

    def save_or_print(self, path, lines, uid=0, gid=0):
        """
        Save lines to path. lines must be newline terminated.
        """
        try:
            with open(path,"w") as file:
                file.writelines(lines)
            if uid and gid:
                os.chown(path, uid, gid)
        except:
            print self.style.NOTICE("Use sudo to modify %s" % path)
            print ''.join(lines)
        

class NoArgsCommand(BaseCommand):
    args = ''

    def handle(self, *args, **options):
        if args:
            raise CommandError("Command doesn't accept any arguments")
        return self.handle_noargs(**options)

    def handle_noargs(self, **options):
        raise NotImplementedError()
    
#try:
#    import paramiko
#except Exception, e:
#    print '*** Paramiko is needed to do remote commands'

class RemoteCommand(BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--verbosity', action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),
            
        make_option('--user', action='store', dest='user', default=None, 
            type='string',
            help='User on remote system (default=root)'),
        make_option('--password', action='store', dest='password', default=None, 
            type='string',
            help='Password to remote system'),
        make_option('--new', action='store_true', dest='new', default=False,
            help='Accept new remote ssh key'),
    )
    args = '<remote remote ...>'
    label = 'remote'
    
    hostport = 22
    username = 'root'
    my_rsa = join(expanduser('~'),'.ssh','id_rsa')
    my_dsa = join(expanduser('~'),'.ssh','id_dsa')
    my_rsa_pub = join(expanduser('~'),'.ssh','id_rsa.pub')

    def load_ssh_hostkeys(self):
        if not exists(self.my_rsa) and not exists(self.my_dsa):
            os.system('ssh-keygen -b 2048 -t rsa') #TODO common call

        with open(self.my_rsa_pub) as rsa_file:
            self.my_rsa_pub_line = rsa_file.readline().strip('\n')

        try:
            self.keys = paramiko.HostKeys(expanduser('~/.ssh/known_hosts'))
        except IOError:
            try:
                self.keys = paramiko.HostKeys(expanduser('~/ssh/known_hosts'))
            except IOError:
                print '*** Unable to open host keys file'
                self.keys = paramiko.HostKeys()
        
    def handle(self, *remotes, **options):
        # setup logging
        
        if hasattr(self,'handle_local'):
            self.handle_local(options)
        if len(remotes):
            #TODO put remote.log in LOG_DIR
            paramiko.util.log_to_file('remote.log')
            self.load_ssh_hostkeys()

        for hostname in remotes:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((hostname, self.hostport))
                transport = paramiko.Transport(sock)
                self.handle_remote(transport, hostname, options)
                transport.close()
            except Exception, e:
                print '*** Connect failed: ' + str(e)
                traceback.print_exc()
                
    def handle_remote(self, transport, hostname, options):
        print '*** interact over transport here for',hostname

def find_commands(management_dir):
    """
    Given a path to a management directory, returns a list of all the command
    names that are available.

    Returns an empty list if no commands are defined.
    """
    command_dir = os.path.join(management_dir, 'commands')
    try:
        return [f[:-3] for f in os.listdir(command_dir)
                if not f.startswith('_') and f.endswith('.py')]
    except OSError:
        return []

def find_command_modules():
    r = []
    for p in sys.path:
        if os.path.isdir(p):
            for pp in os.listdir(p):
                cp = os.path.join(p,pp,'commands')
                if os.path.isdir(cp): r.append(pp)
    return r
        
def get_mod_path(name):
    i = __import__(name,{},{},[])
    return i.__path__[0]

class LaxOptionParser(OptionParser):
    """
    An option parser that doesn't raise any errors on unknown options.

    This is needed because the --settings and --pythonpath options affect
    the commands (and thus the options) that are available to the user.
    """
    def error(self, msg):
        pass

class CommandWrapper(object):

    def __init__(self,cmd=None,base=None,name=None):
        self._cmd = cmd
        self.base = base
        self.name = name
        
    def get_cmd(self):
        """
        Instantiate the command if not yet loade. All errors raised by the import process
        (ImportError, AttributeError) are allowed to propagate.
        """
        if not self._cmd:
            self._cmd = getattr(__import__('%s.commands.%s' % (self.base, self.name),
                {}, {}, ['Command']), 'Command')()
        return self._cmd
    cmd = property(get_cmd)
    
    def get_option_list(self):
        return getattr(self.cmd,'option_list',BaseCommand.option_list)
    option_list = property(get_option_list)
    
    def get_help(self):
        return getattr(self.cmd,'help',BaseCommand.help)
    help = property(get_help)
    
    def get_args(self):
        return getattr(self.cmd,'args',BaseCommand.args)
    args = property(get_args)
    
    def get_style(self):
        return getattr(self.cmd,'style',color_style())
    style = property(get_style)
    
    
    def get_version(self):
        if hasattr(self.cmd,'get_version'):
            return self.cmd.get_version()
        import thepian
        return thepian.VERSION

    def usage(self, subcommand):
        if hasattr(self.cmd,'usage'):
            return self.cmd.usage(subcommand)
            
        usage = self.style.HEADING('%%prog %s [options] %s' % (subcommand, self.args))
        if self.help:
            return '%s\n\n%s' % (usage, self.style.HIGHLIGHT(self.help))
        else:
            return usage

    def create_parser(self, prog_name, subcommand):
        if hasattr(self.cmd,'create_parser'):
            return self.cmd.create_parser(prog_name,subcommand)
            
        return OptionParser(prog=prog_name,
                            usage=self.usage(subcommand),
                            version=self.get_version(),
                            option_list=self.option_list)

    def print_help(self, prog_name, subcommand):
        if hasattr(self.cmd,'print_help'):
            return self.cmd.print_help(prog_name,subcommand)
            
        parser = self.create_parser(prog_name, subcommand)
        parser.print_help()

    def run_from_argv(self, argv):
        """Run directly from command line arg list, ignores run_from_argv on the command to handle default options properly"""
        parser = self.create_parser(argv[0], argv[1])
        options, args = parser.parse_args(argv[2:])
        self(*args, **options.__dict__)
    
    def __call__(self, *args, **options):
        if hasattr(self.cmd,'__call__'):
            return self.cmd(*args,**options)    
        if hasattr(self.cmd,'execute'):
            return self.cmd.execute(*args,**options)    
        if hasattr(self.cmd,'handle'):
            return self.cmd.handle(*args,**options)    
        print 'cannot execute command' #TODO raise?

class HelpWrapper(CommandWrapper):
    """Not sure if this should replace the special help handling"""
    #TODO
    pass
    
class Cmds(object):
    cache = None
    load_user_commands = True
    
    def get_commands(self):
        """
        Returns a dictionary mapping command names to their command wrappers noting the base module.
    
        This works by looking for a commands package in thepian.cmdline, and
        in each top level package -- if a commands package exists, all commands
        in that package are registered.
    
        If a specific version of a command must be loaded (e.g., with the
        startapp command), the instantiated module can be placed in the
        dictionary in place of the application name.
    
        The dictionary is cached on the first call and reused on subsequent
        calls.
        """
        if self.cache is None:
            self.cache = { 'help' : HelpWrapper() }
            if self.load_user_commands:
                # Add any top level packages with commands submodules
                for mod in find_command_modules():
                    try:
                        cmd_and_wrapper = [(name,CommandWrapper(base=mod,name=name)) for name in find_commands(get_mod_path(mod))]
                        self.cache.update(dict(cmd_and_wrapper))
                    except ImportError,e:
                        print "Error while checking module '%s'" % mod, e
                
        return self.cache
    
    def __getitem__(self,name):
        try:
            cmds = self.get_commands()
            return cmds[name]
        except KeyError:
            raise CommandError, "Unknown command: %r" % name
            
    def __contains__(self,name):
        cmds = self.get_commands()
        return name in cmds
        
    def main_help_text(self,argv=None):
        """
        Returns the script's main help text, as a string.
        """
        import thepian
        prog_name = os.path.basename(argv[0])
        style = color_style()
        usage = [
            style.HEADING('%s <subcommand> [options] [args]' % prog_name),
            'Thepian command line tool, version %s' % thepian.get_version(),
            "Type '%s help <subcommand>' for help on a specific subcommand." % prog_name,
            'Available subcommands:',
        ]
        commands = self.get_commands().keys()
        commands.sort()
        return '\n'.join(usage + ['  %s' % cmd for cmd in commands])

    def execute(self,argv=None):
        """
        Given the command-line arguments, this figures out which subcommand is
        being run, creates a parser appropriate to that command, and runs it.
        """
        argv = argv or sys.argv[:]
        prog_name = os.path.basename(argv[0])
        
        try:
            subcommand = argv[1]
        except IndexError:
            sys.stderr.write("Type '%s help' for usage.\n" % prog_name)
            sys.exit(1)
        
        try:
            if subcommand == 'help':
                import thepian
                parser = LaxOptionParser(version=thepian.get_version(), option_list=BaseCommand.option_list)
                options, args = parser.parse_args(argv)
                if len(args) > 2:
                    self[args[2]].print_help(prog_name, args[2])
                else:
                    sys.stderr.write(self.main_help_text(argv) + '\n')
                    sys.exit(1)
            else:
                wrapper = self[subcommand]
                if getattr(wrapper.cmd,'requires_machine',False):
                    from thepian.conf import structure
                    if not structure.machine.known:
                        sys.stderr.write('Machine is not known (mac %s), cannot execute %s\n' % (structure.machine['mac'],repr(wrapper.cmd)))
                        return
                        #TODO return error code
                wrapper.run_from_argv(argv)

        except CommandError, e:
            sys.stderr.write("%s\nType '%s help' for usage\n" % (e.message,os.path.basename(argv[0])))
            #TODO return error code


