from __future__ import with_statement

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.template import Lexer, TOKEN_TEXT, TOKEN_BLOCK, TOKEN_VAR, TemplateDoesNotExist
from django.template.loader import render_to_string
from django.template.loaders import filesystem, app_directories
from django.utils.encoding import smart_unicode
from thepian.utils.jsmin import jsmin
from os.path import exists, getmtime, join
from popen2 import popen2
from sha import sha
import os
import re

from thepian.conf import structure

__VERSION__ = 0, 1, 0

_COMPRESS_JAVASCRIPT = getattr(settings, 'TEMPLATEASSETS_COMPRESS_JAVASCRIPT', not settings.DEBUG)
_COMPRESS_CSS = getattr(settings, 'TEMPLATEASSETS_COMPRESS_CSS', not settings.DEBUG)

compress_js = jsmin

try:
    _YUICOMPRESSOR_JAR = structure.TOOLS_DIR + "/lib/yuicompressor-2.4.1.jar"
    if not exists(_YUICOMPRESSOR_JAR):
        raise ImproperlyConfigured, _YUICOMPRESSOR_JAR + " not found."

    _YUICOMPRESSOR_OPTIONS = getattr(settings, 'TEMPLATEASSETS_OPTIONS', '')

    def _compress_yui(string, typ):
        cmdline = "java -jar %s --type %s %s" % (_YUICOMPRESSOR_JAR, typ, _YUICOMPRESSOR_OPTIONS)
        readstream, writestream = popen2(cmdline)
        writestream.write(string)
        writestream.close()
        return readstream.read()

    compress_js = lambda s: _compress_yui(s, 'js')
    compress_css = lambda s: _compress_yui(s, 'css')

except AttributeError:
    if _COMPRESS_CSS:
        raise ImproperlyConfigured, (
          'To use css compression, you need to specify a full path to yuicompressor.jar'
          'using settings.TEMPLATEASSETS_PATH_TO_YUICOMPRESSOR_JAR'
        )

if not _COMPRESS_CSS:
    compress_css = lambda s: s

if not _COMPRESS_JAVASCRIPT:
    compress_js = lambda s: s

# These variables will be expanded     
VAR_EXPANSIONS = {

    'MEDIA_URL' : settings.MEDIA_URL,

}
    
def _parse_asset_parameters(parameters):
    blocktag = parameters[0]
    parameters = parameters[1:]
    priority = 0
    groups = []
    for p in parameters:
        try:
            priority = int(p)
        except ValueError:
            groups.append(p)

    return {
      'priority': priority,
      'groups': groups,
      'blocktag': blocktag,
    }



class TemplateFile(object):
    
    content_hash = None
    extends = None
    
    def __init__(self,dirpath,filename,templatedir=""):
        if templatedir and dirpath.startswith(templatedir):
            dirpath = dirpath[len(templatedir)+1:]
        self.dirpath = dirpath
        self.filename = filename
        self.templatepath = join(self.dirpath,self.filename)
        self.templatedir = templatedir
        
    def __repr__(self):
        return self.__str__()
        
    def __unicode__(self):
        return unicode(self.__str__())
        
    def __str__(self):
        return self.templatepath
        
    def __hash__(self):
        return hash(str(self))
        
    def __eq__(self,other):
        try:
            return str(self) == str(other)
        except AttributeError:
            return false
            
    def bases(self):
        b = []
        e = self.extends
        while e:
            b.append(e)
            e = e.extends
        return b
        
        
    def load_blocks(self):
        """Loads the asset blocks defined in the template
        handles:
         * extends - to track template hierachy
         * css,javascript - start of asset
         * endcss, endjavascript - end of asset
         * {{ .. }} - expansion of variables to settings variables according to VAR_EXPANSIONS
         """
        try:
            template_string, _filepath = filesystem.load_template_source(self.templatepath)
        except TemplateDoesNotExist:
            template_string, _filepath = app_directories.load_template_source(self.templatepath)

        self.content_hash = hash(template_string)

        try:
            result = TemplateAssetBucket()

            l = Lexer(template_string, self.templatepath)
            within = None
            texts = []
            for m in l.tokenize():
                if m.token_type == TOKEN_BLOCK:
                    split = m.split_contents()
                    typ = split[0]

                    if typ == "extends":
                        if split[1].endswith('"') or split[1].endswith("'"):
                            self.extends = split[1].strip('"').strip("'")
                        else:
                            pass #TODO figure out support for variable expansion
                    elif typ in TemplateAssetBlock.BLOCKTAGS:
                        within = typ
                        prop = _parse_asset_parameters(m.split_contents())
                    elif typ.startswith('end'):
                        if typ[3:] == within:
                            within = None
                            result.append(TemplateAssetBlock(''.join(texts), template=self, **prop))
                        elif typ[3:] in TemplateAssetBlock.BLOCKTAGS:
                            assert false, "encountered dangling %s tag in '%s'" % (typ,self.templatepath)
                elif within:
                    if m.token_type == TOKEN_TEXT:
                        texts.append(m.contents)
                    elif m.token_type == TOKEN_VAR:
                        v = VAR_EXPANSIONS.get(m.contents,'')
                        if v:
                            texts.append(v)
                        #? else:
                        #assert False, "Variable replacement in client side magic not yet supported"

            return result
        except UnicodeDecodeError:
            return "/* could not load %s as a template */\n" % templatepath


def tree_sorter(x,y):
    X_FIRST = -1
    Y_FIRST = +1
    xt,yt = x.template,y.template
    
    if not xt.extends and yt.extends:
        return X_FIRST
    if xt.extends and not yt.extends:
        return Y_FIRST
    if xt.extends and yt.extends:
        if xt in yt.bases():
            return X_FIRST
        if yt in xt.bases():
            return Y_FIRST
    return y.priority - x.priority

class TemplateAssetBucket(list):
    
    def __repr__(self):
        return self.__str__()

    def __str__(self):
        #self.sort(lambda x, y: y.priority - x.priority)
        self.sort(tree_sorter)
        return "\n".join(str(b) for b in self)
        
    def available(self):
        sofar = set()
        for block in self.without_inline():
            for group in block.groups:
                sofar.add((group, block.blocktag))

        return list(sofar)

    def without_inline(self):
        return TemplateAssetBucket(
          block for block in self if 'inline' not in block.groups
        )

    def filter(self, t):
        assert t in TemplateAssetBlock.BLOCKTAGS
        return TemplateAssetBucket(
          block for block in self if block.blocktag == t
        )

    def group(self, group):
        if group == None:
            return TemplateAssetBucket(
              block for block in self if len(block.groups) == 0
            )

        return TemplateAssetBucket(
          block for block in self if group in block.groups
        )

    def compress(self):
        if len(self) == 0:
            return ''

        typ = self[0].blocktag

        for b in self:
            assert b.blocktag == typ, 'Must be of same type!'

        if typ == 'javascript':
            return compress_js(str(self))
        elif typ == 'css':
            return compress_css(str(self))

        assert False, 'never reach this'


class TemplateAssetBlock:

    # The TemplateFile
    template = None
    
    BLOCKTAGS = 'css', 'javascript'

    def __init__(self, text, blocktag, groups=[], priority=0, origin='', template=None):
        self.text = text.strip()
        self.blocktag = blocktag
        self.priority = priority
        self.template = template
        self.origin = origin or template and template.templatepath or ''

        if 'inline' in groups and len(groups) > 1:
            raise ImproperlyConfigured, (
              "Error in %s: If a template component block has "
              "group inline, it can't have other groups.") % self.origin

        self.groups = groups

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"/* extracted %s%s%s%s */\n%s" % self._tuple_repr()

    def __str__(self):
        return "/* extracted %s%s%s%s */\n%s" % self._tuple_repr()
        
    def _tuple_repr(self):
        return (
            self.blocktag, 
            self.origin and " from template '%s'" % self.origin or '',
            self.priority and ' with priority %d' % self.priority or '', 
            self.groups and ' with groups ' + ', '.join(self.groups) or '', 
            self.text
        )

_all = None #TODO check changes on a timer, and clear this if needed

def all():
    global _all
    if _all:
        return _all
        
    unknown_templates = set()
    pile = TemplateAssetBucket()
    templates = all_templates()
    #print u"\n".join(unicode(templates[n]) for n in templates)
    for n in templates:
        template = templates[n]
        try:
            #old_blocks = existing_pile.get_blocks(template)
            new_blocks = template.load_blocks()
            if template.extends:
                try:
                    template.extends = templates[template.extends]
                except KeyError:
                    unknown_templates.add(template.extends)
                    template.extends = None
            pile.extend(new_blocks)
            #pile.adjust(new_blocks,old_blocks)
        except UnicodeDecodeError, e:
            print 'Skipped %s , %s' % (str(template),e)

    additional = getattr(settings, 'TEMPLATEASSETS_ADDITIONAL', {})
    #TODO compile /src/main/css & /src/main/js
    for path, parameters in additional.items():
        if not os.path.exists(path):
            raise ImproperlyConfigured, "%s was not found, but specified in settings.TEMPLATEASSETS_ADDITIONAL"
        with open(path) as f:
            block = TemplateAssetBlock(f.read(), origin=path, **_parse_asset_parameters(parameters.split(" ")))
        pile.append(block)

    if len(unknown_templates):
        print "warning: Failed to find templates: %s" % ', '.join(unknown_templates)
    
    _all = pile
    
    return pile


EXCLUDE_SUBDIRS = ('.svn', '.*.swp$', '*.~$', '.git')

def all_templates(ignore_dot_files=True):
    """Gets a list of all template file paths as TemplateFile instances.
    Supports filesystem and app_directories loaders"""
    all = {}

    if 'django.template.loaders.filesystem.load_template_source' in settings.TEMPLATE_LOADERS:
        for templatedir in settings.TEMPLATE_DIRS:
            for dirname, subdirs, regular in os.walk(templatedir):
                for exclude in EXCLUDE_SUBDIRS:
                    if exclude in subdirs:      # Remove the EXCLUDE subdirs, so they wont be walked (don't do bottom up!!)
                        del subdirs[exclude]
                for filename in regular:
                    if ignore_dot_files and filename[0] == ".":
                        continue
                    t = TemplateFile(dirname,filename,templatedir=templatedir)
                    all[unicode(t)] = t
    if 'django.template.loaders.app_directories.load_template_source' in settings.TEMPLATE_LOADERS:
        from django.template.loaders.app_directories import app_template_dirs
        for templatedir in app_template_dirs:
            for dirname, subdirs, regular in os.walk(templatedir):
                for exclude in EXCLUDE_SUBDIRS:
                    if exclude in subdirs:      # Remove the EXCLUDE subdirs, so they wont be walked (don't do bottom up!!)
                        del subdirs[exclude]
                for filename in regular:
                    if ignore_dot_files and filename[0] == ".":
                        continue
                    t = TemplateFile(dirname,filename,templatedir=templatedir)
                    all[unicode(t)] = t

    return all
