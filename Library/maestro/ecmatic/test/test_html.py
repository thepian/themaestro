from __future__ import with_statement

import unittest

from ecmatic.html import Grammar    

class GrammarTestCase(unittest.TestCase):
    
    def test_whitespace(self):
        g = Grammar("<html> </html>")
        result,error = g.apply("html")
        assert result == [["html", {}, [" "]]]

        g = Grammar(" <html> </html>")
        result,error = g.apply("html")
        assert result == [" ",["html", {}, [" "]]]

        g = Grammar("< html> </html >")
        result,error = g.apply("html")
        assert result == [["html", {}, [" "]]]

        g = Grammar("<html> </ html>")
        result,error = g.apply("html")
        assert result == [["html", {}, [" "]]]

        g = Grammar("<html > < /html>")
        result,error = g.apply("html")
        assert result == [["html", {}, [" "]]]

        g = Grammar("""
   <html> </html>""")
        result,error = g.apply("html")
        assert result == ["\n   ",["html", {}, [" "]]]

    def test_html_language(self):
        g = Grammar("<html language='en'> </html>")
        result,error = g.apply("html")
        assert result == [["html", { 'language':'en' }, [" "]]]

    def test_string_attr(self):
        g = Grammar('a="b"')
        result, error = g.apply("string_attribute")
        assert result == ("a","b") 

        g = Grammar('a="b" c="d"')
        result, error = g.apply("attributes")
        assert result == { "a":"b", "c":"d" } 

    def test_bool_attr(self):
        g = Grammar('a')
        result, error = g.apply("bool_attribute")
        assert result == ("a",True) 

        g = Grammar('a c')
        result, error = g.apply("attributes")
        assert result == { "a":True, "c":True } 

        g = Grammar("""\
<html><body><input disabled ></input></body></html>
""")
        result,error = g.apply("html")
        print error
        assert result == [
            ["html", {}, [
                ['body', {}, [['input', { "disabled":True }, [] ]]]
                ]],
            '\n']

    def notest_doctype(self):
         g = Grammar("""\
<|DOCTYPE html>
<html> </html>""")
         result,error = g.apply("html")
         assert result == [["html", {}, [" "]]]
        