from __future__ import with_statement
import os, re
from os.path import join,isdir,exists
from thepian.conf import structure

from sources import CssSourceNode,JsSourceNode, newer_assets, combine_asset_sources

class VerifySource(object):
    
    sources = {}
    
    @classmethod
    def get(cls,base,name):
        path = join(base,name+".html")
        js_path = join(base,name+".js")
        if path not in cls.sources:
            cls.sources[path] = VerifySource(name[:-3],path = path,js_path = js_path)
        return cls.sources[path]
    
    @classmethod
    def list(cls,base):
        tests = os.listdir(base)
        specs = []
        for test in tests:
            if test.endswith(".js"):
                specs.append(cls.get(base,test))
        return specs
        
    
    verify_template = """
%(lead)s
<form id="results" action="%(form_action)s" method="post" >
	%(xsrf_form_html)s
	{% for spec in specs %}
	<input type="hidden" name="{{ spec.name }}-result" value="">
	{% end %}
</form>
<script type="text/javascript">
%(script)s
%(verify_script)s
</script>
%(tail)s
"""
    
    def __init__(self,name,path,js_path,source=None):
        self.name = name
        self.path = path
        self.js_path = js_path
        self.source = source
        self.load()
            
    type_regex = re.compile(r"""\btype="(\w*/\w*)"\b""")
    language_regex = re.compile(r"""\blanguage="(\w*)"\b""")
    src_regex = re.compile(r"""\bsrc="([^"]*)"\b""")

    def get_attr(self,regex,attrs):
        """Determine the attribute contents"""
        if not attrs: return None
        found = regex.search(attrs)
        if found:
            return found.group(1)
        return None

    def reload(self):
        self.source = None
        self.load()
        
    def load(self):
        if self.source is None and exists(join(structure.JS_DIR,self.path)):
            with open(join(structure.JS_DIR,self.path)) as f:
                self.source = f.read()
                
        import html5lib
        from xml.etree import ElementTree
        # parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilders("dom"))
        parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("etree", ElementTree))
        self.doc = parser.parse(self.source)
        scripts = self.doc.getiterator("script")
        self.scripts = []
        for script in scripts:
            if script.attrib["type"] == "text/pagespec" and "language" in script.attrib:
                if "src" in script.attrib:
                    pass #TODO load the file
                script.parent.remove(script)
                self.scripts.append(script)
        self.tail_script = ElementTree.SubElement(self.doc.find("body"),"script", type="text/javascript")
                    
        

    script_regex = re.compile(r"""<(/?)script([^>]*)(/?)>""")

    def old_load(self):
        if self.source is None and exists(join(structure.JS_DIR,self.path)):
            with open(join(structure.JS_DIR,self.path)) as f:
                self.source = f.read()
                
        scripts = [i for i in self.script_regex.finditer(self.source)]
        self.scripts = []
        for script,next in zip(scripts, scripts[1:]):
            src = self.get_attr(self.src_regex,script.group(2))
            tp = self.get_attr(self.type_regex,script.group(2))
            print script.groups(), src, tp
            if tp == "text/pagespec":
                if script.group(3) == "" or src: # single tag, or script.src=?
                    pass #TODO
                elif script.group(1) == "": #beginning tag
                    language = self.get_attr(self.language_regex,script.group(2))
                    if language:
                        self.scripts.append({
                            "language": language,
                            "source": self.source[script.end()+1 : next.start()-1]
                        })
            
            
    def render(self,form_action="",xsrf_form_html=""):
        language = self.get_language(self.script)
        if language == "verify":
            src = join(structure.JS_DIR,self.js_path)
            lines = combine_asset_sources(src,structure.JS_DIR,source_node=JsSourceNode)
            info = {
                "form_action": form_action,
                "xsrf_form_html": xsrf_form_html,
                "script": '\n'.join(lines),
                "verify_script": self.script.group(3),
                "lead": self.source[:self.script.start()],
                "tail": self.source[self.script.end():]
            }
            return self.verify_template % info
        else:
            return self.source


        
    

