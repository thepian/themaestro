from thepian.conf import structure
from mediaserver.sources.js import JsSourceNode

decorated_source = """\
/* @scope "test.scope.js" */
var stuff = "stuff";
"""
decorated_result = """\
(function(){
%s
})();""" % decorated_source

def test_decorated_lines():
    js = JsSourceNode('',structure.JS_DIR,source=decorated_source)
    decorated = js.decorated_lines()
    assert '\n'.join(decorated) == decorated_result