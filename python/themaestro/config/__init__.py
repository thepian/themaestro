import re
import fs
from os.path import dirname,abspath,join,split,exists,expanduser,isfile
import shutil

def copy_template(style, template_prefix, name, directory, other_name=''):
    """
    Copies either a Thepian application layout template or a Thepian project
    layout template into the specified directory.
    """
    # style -- A color style object (see django.core.management.color).
    # template_prefix -- The string 'app' or 'project'.
    # name -- The name of the application or project.
    # directory -- The directory to which the layout template should be copied.
    # other_name -- When copying an application layout, this should be the name
    #               of the project.
    import devonly.conf
    from thepian.conf import structure
    from thepian.utils.fs import make_writeable
    if not re.search(r'^\w+$', name): # If it's not a valid directory name.
        raise CommandError("%r is not a valid %s name. Please use only numbers, letters and underscores." % (name, template_name))

    template_name = template_prefix + "_template"
    try:
        template_dir = join(devonly.conf.__path__[0],template_name)
        for d, subdirs, files in fs.walk(template_dir):
            relative_dir = d[len(template_dir)+1:].replace('%s_name' % template_prefix, name)
            if relative_dir:
                fs.makedirs(join(directory, relative_dir))
            for i, subdir in enumerate(subdirs):    # this bit seems to serve no purpose
                if subdir.startswith('.'):
                    del subdirs[i]
            for f in files:
                if f.endswith('.pyc'):
                    continue
                if f.startswith('.'):
                    continue
                path_old = join(d, f)
                path_new = join(directory, relative_dir, f)
                fp_old = open(path_old, 'r')
                fp_new = open(path_new, 'w')
                fp_new.write(fp_old.read().replace('{{ project_name }}', name)
                                          .replace('{{ admin_name }}',structure.ADMIN_NAME)
                                          .replace('{{ admin_email }}',structure.ADMIN_EMAIL)
                                          .replace('{{ dev_machines }}', str(structure.DEV_MACHINES))
                                          .replace('{{ django_port }}', str(structure.DJANGO_PORT))
                                          )
                fp_old.close()
                fp_new.close()
                try:
                    shutil.copymode(path_old, path_new)
                    make_writeable(path_new)
                except OSError:
                    sys.stderr.write(style.NOTICE("Notice: Couldn't set permission bits on %s. You're probably using an uncommon filesystem setup. No problem.\n" % path_new))
    except Exception,e:
        print "Skipping '%s', not found (%s)" % (template_name,e)
