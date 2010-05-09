import re
from mediaserver.verify import *

def test_load():
    just_script = """<!DOCTYPE html>
<html>
<head>
	<title>{{ title }}</title>
</head>
<body>
	<h1>{{ title }}</h1>

	<script type="text/pagespec" language="verify" >

		@include("pagecore/core.js");

		@include("pagecore/verify/core.js");
	</script>
</body>
</html>
"""
    verify = VerifySource('file','file/verify/file.html','file.js',just_script)
    assert verify.doc != None
    assert len(verify.scripts) == 1
    
def notest_re():
    just_script = """<script type="text/pagespec" language="verify" >
stuff
</script>"""

    verify = VerifySource('file','file/verify/file.html','file.js',just_script)
    assert verify.get_attr(VerifySource.language_regex,'language="a"') == "a"
    assert verify.get_attr(VerifySource.type_regex,'type="a"') == "a"
    assert len(verify.scripts) == 2
    # assert VerifySource.pagespec_script.search(just_script) != None