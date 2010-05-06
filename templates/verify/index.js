(function(){
    var form = document.forms[0];
    
    // make unique identifier ?
    var unique_id = new Date().getTime(); //TODO combine with local ip
    form.action = String(unique_id); // unique url
    
    var result = [];
    var assertCount = 0;
    
    function assertIdentical(expect,v) {
        ++assertCount;
        if (expect !== v) {
            result.push("failed assert ("+assertCount+"): expected <"+expect+"> was <"+v+">");
        }
    }

    function assertSame(expect,v) {
        ++assertCount;
        if (expect != v) {
            result.push("failed assert ("+assertCount+"): expected <"+expect+"> was <"+v+">");
        }
    }
    
    function assertTrue(a) {
        assertSame(true,arguments[arguments.length-1]);
    }
    function assertFalse(a) {
        assertSame(false,arguments[arguments.length-1]);
    }
    function assertNull(a) {
        assertSame(null,arguments[arguments.length-1]);
    }
    function assertEquals(a,b) {
        assertSame(arguments[arguments.length-2],arguments[arguments.length-1]);
    }
    
{% for spec in specs %}
(function(){
result = [];
assertCount = 0;
try {
    {{ spec.source }}
}
catch(ex) {
    result.push("exception: "+ex);
}
var resultEl = document.getElementsByName("{{spec.name}}-result")[0];
resultEl.value = result.join('\n');
})();
{% end %}
    
    form.submit();
})();
