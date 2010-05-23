from thepian.conf import structure
from mediaserver.sources.js import JsSourceNode


def test_decorated():
    js = JsSourceNode('',structure.JS_DIR,source='x;')
    
    assert js.decorated(' @stash("abc",abc); ') == " \n__folded_abc__ = abc;\n "
    assert "abc" in js.stashes

    assert js.decorated(' @stash("map",{ "one":1, "two":2 }); ') == ' \n__folded_map__ = { "one":1, "two":2 };\n '
    assert "map" in js.stashes

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