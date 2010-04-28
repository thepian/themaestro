import os, site
from itertools import dropwhile
from optparse import make_option
from thepian.cmdline.base import ThepianCommand, CommandError, BaseCommand



class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--locale', '-l', default=None, dest='locale',
            help='Creates or updates the message files only for the given locale (e.g. pt_BR).'),
        make_option('--domain', '-d', default='django', dest='domain',
            help='The domain of the message files (default: "django").'),
        make_option('--verbosity', '-v', action='store', dest='verbosity',
            default='1', type='choice', choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),
        make_option('--all', '-a', action='store_true', dest='all',
            default=False, help='Reexamines all source code and templates for new translation strings and updates all message files for all available languages.'),
        make_option('--extension', '-e', dest='extensions',
            help='The file extension(s) to examine (default: ".html", separate multiple extensions with commas, or use -e multiple times)',
            action='append'),
    )
    help = "Runs over the entire source tree of the current directory and pulls out all strings marked for translation. It creates (or updates) a message file in the conf/locale (in the django tree) or locale (for project and application) directory."

    requires_model_validation = False
    can_import_settings = False

    def handle(self, *args, **options):
        from thepian.conf import import_structure
        structure = import_structure(os.getcwd())
        try:
            import django
        except ImportError:
            if structure.DEVELOPING:
                site.addsitedir(structure.LIB_DIR)
        import django
        from django.core.management.commands.makemessages import make_messages, handle_extensions
            
        if len(args) != 0:
            raise CommandError("Command doesn't accept any arguments")

        locale = options.get('locale')
        domain = options.get('domain')
        verbosity = int(options.get('verbosity'))
        process_all = options.get('all')
        extensions = options.get('extensions') or ['html']

        if domain == 'djangojs':
            extensions = []
        else:
            extensions = handle_extensions(extensions)

        if '.js' in extensions:
            raise CommandError("JavaScript files should be examined by using the special 'djangojs' domain only.")

        #old_cwd = os.getcwd()
        #os.chdir(os.path.dirname(django.__file__))
        make_messages(locale, domain, verbosity, process_all, extensions)
        #os.chdir(old_cwd)
