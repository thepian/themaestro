import sys,os,stat
from os.path import exists, lexists, join

def make_executable(filename):
    "Makes sure that the file is executable."
    import stat
    if sys.platform.startswith('java'):
        # On Jython there is no os.access()
        return
    if not os.access(filename, os.X_OK):
        st = os.stat(filename)
        new_permissions = stat.S_IMODE(st.st_mode) | stat.S_IEXEC | stat.S_IXGRP
        os.chmod(filename, new_permissions)

def make_writeable(filename):
    "Makes sure that the file is writeable. Useful if our source is read-only."
    import stat
    if sys.platform.startswith('java'):
        # On Jython there is no os.access()
        return
    if not os.access(filename, os.W_OK):
        st = os.stat(filename)
        new_permissions = stat.S_IMODE(st.st_mode) | stat.S_IWUSR
        os.chmod(filename, new_permissions)

def makedirs(*elements):
    dirs = join(*elements)
    if not exists(dirs):
        os.makedirs(dirs)

def makedirs_tree(base_dir,dirs):
    """
    Take a list of directory names(string or tuple) and create a tree in base_dir
    """
    for dir in dirs:
        if type(dir) == tuple: dir = join(dir)
        dir = join(base_dir,dir)
        if not exists(dir):
            os.makedirs(dir)
            
def require_directory(path, uid, gid, mod = stat.S_IRUSR+stat.S_IWUSR+stat.S_IXUSR+stat.S_IRGRP+stat.S_IWGRP+stat.S_IXGRP+stat.S_IROTH+stat.S_IXOTH):
    """default mod = user:rwx group:rwx other:rx"""
    makedirs(path)
    os.chown(path, uid, gid)
    os.chmod(path, mod)


def ensure_symlink(src,dest,replace=True):
    if lexists(dest):
        if not replace:
            return
        os.remove(dest)
    os.symlink(src,dest)
    
def ensure_link(src,dest,replace=True):
    if exists(dest):
        if not replace:
            return
        os.remove(dest)
    os.link(src,dest)
    
def first_exists(name_list):
    """Return the first file or directory in the supplied list that exists"""
    for fn in name_list:
        if exists(fn):
            return fn
    return None
