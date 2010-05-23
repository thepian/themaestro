from mediaserver.sources import expand_inline_asset_sources, JsSourceNode
from thepian.conf import structure

decorated_source = """\
/* @scope "test.scope.js" */
var stuff = "stuff";
"""
result = """\
/* %s */

(function(){
%s
})();


"""

def test_scoping():
    script_string = 'var stuff = "stuff";'
    attributes = {}
    lines = expand_inline_asset_sources(script_string,structure.JS_DIR, attributes=attributes, source_node=JsSourceNode, default_scope = 'test.scope.js')
    assert '\n'.join(lines) == result % ('',script_string)