from __future__ import with_statement
import fs, re
from fs.filters import fnmatch
from os.path import join,isdir,exists

from thepian.conf import structure

from base import SourceNode
import cssutils

def css_fetcher(url):
    #print url
    read = u''
    with open(url[7:],"r") as f:
        read = f.read()
    return None, u"/* imported */" + unicode(read)

# from cssutils.profiles import macros as predef
# import cssutils.profile
# macros = {'my-font': predef[profile.CSS_LEVEL_2]['family-name'],
#           'identifier': predef[profile.CSS_LEVEL_2]['identifier']}
# props = {'f': '{my-font}'}
# cssutils.profile.addProfile('my-font-profile', props, macros)
            
class CssSourceNode(SourceNode):
    
    @classmethod
    def list_sources(cls,src,full_path=True):
        return fs.listdir(src,full_path=True,recursed=False,filters=(fnmatch("*.css"),))
        
    def get_lines(self):
        css = u''.join(self._lines)
        parser = cssutils.CSSParser(fetcher=css_fetcher)
        sheet = parser.parseString(css,href="file://"+self.path)
        cssutils.ser.prefs.useMinified()
        cssutils.ser.prefs.keepComments = False
        sheet = cssutils.resolveImports(sheet)
        return [u'%s\n' % rule.cssText for rule in sheet if rule.cssText and len(rule.cssText)>0]
    lines = property(get_lines)
       
