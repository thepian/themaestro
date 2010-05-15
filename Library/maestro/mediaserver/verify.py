from __future__ import with_statement
import os, re
from os.path import join,isdir,exists
from thepian.conf import structure

from sources import CssSourceNode,JsSourceNode, newer_assets, combine_asset_sources, expand_inline_asset_sources

import simplejson
    
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
    def discard(cls,base,name):
        path = join(base,name+".html")
        if path in cls.sources:
            del cls.sources[path]
    
    @classmethod
    def list(cls,base):
        tests = os.listdir(base)
        specs = []
        for test in tests:
            if test.endswith(".js"):
                specs.append(cls.get(base,test))
        return specs

    decoder = simplejson.JSONDecoder()
    
    @classmethod
    def posted_results(cls,arguments):
        results = []
        for key in arguments.keys():
            if key.endswith("-result"):
                print arguments[key]
                results.append((key[:-7],cls.decoder.decode(arguments[key])))
    
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

        from BeautifulSoup import BeautifulSoup, Tag
        soup = BeautifulSoup(self.source)
        scripts = soup.findAll('script',type="text/pagespec", language=re.compile('.+'))
        specs = []
        form_result_names = []
        index = 1
        for script in scripts:
            # script["name"] or index counter
            attributes = {
                "language" : script["language"],
                "type" : script["type"]
            }
            if "id" in script:
                attributes["id"] = script["id"]
            if "name" in script:
                attributes["name"] = script["name"]
            else:
                attributes["name"] = script["language"] + str(index)
            attributes["result_name"] = attributes["name"] + "-result"
            form_result_names.append(attributes["result_name"])
            lines = expand_inline_asset_sources(script.string,structure.JS_DIR, attributes=attributes, source_node=JsSourceNode, default_scope = 'verify/inner.scope.js')
            specs.append('\n'.join(lines)) #TODO do lines end with \n ?
            script.extract()
            ++index
            
        #TODO improve the decorate_lines interface
        JsSourceNode.decorate_lines(specs,[JsSourceNode('','',source='')],basedir=structure.JS_DIR,default_scope="verify/outer.scope.js")

        new_form = Tag(soup, "form", attrs=[("id","results"),("method","post")])
        xsrf_input = Tag(soup, "input", attrs=[("type","hidden"),("name","_xsrf"),("value","")])
        new_form.append(xsrf_input)
        self.xsrf_input = xsrf_input
        new_form.insert(0,'<button type="submit">Submit result</button>')
        for name in form_result_names:
            new_form.insert(0,'<input type="hidden" name="%s" value="">' % name)
        soup.body.append(new_form)

        soup.body.append("\n");
        
        new_script = Tag(soup, "script", attrs=[("type","text/javascript")])
        new_script.insert(0, '\n'.join(specs))
        soup.body.append(new_script)

        self.soup = soup
        self.new_form = new_form
        self.new_script = new_script
        
    def simple_load(self):
        if self.source is None and exists(join(structure.JS_DIR,self.path)):
            with open(join(structure.JS_DIR,self.path)) as f:
                self.source = f.read()
                
        import html5lib
        self.doc = html5lib.parse(self.source)
        scripts = self.doc.getiterator("script")
        self.scripts = []
        for script in scripts:
            if script.attrib["type"] == "text/pagespec" and "language" in script.attrib:
                if "src" in script.attrib:
                    pass #TODO load the file
                script.parent.remove(script)
                self.scripts.append(script)
        self.tail_script = ElementTree.SubElement(self.doc.find("body"),"script", type="text/javascript")
        
    def five_load(self):
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
                    
                    
    def render(self,form_action="",xsrf_token=""):
        
        self.new_form["action"] = form_action
        self.xsrf_input["value"] = xsrf_token

        morphed = self.soup.prettify()
        # print morphed
        return morphed


        
    

