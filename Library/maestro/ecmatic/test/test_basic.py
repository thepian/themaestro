from __future__ import with_statement

import unittest

from ecmatic.basic import Grammar    

class GrammarTestCase(unittest.TestCase):
    
    def test_comment(self):
        g = Grammar("""\
// hello""")
        result,error = g.apply("comment")
        assert result == ["comment", " hello"]

        g = Grammar("""/*
*/""")
        result,error = g.apply("mlcomment")
        assert result == ['mlcomment',"\n"]

        g = Grammar("""/***
///
***/""")
        result,error = g.apply("mlcomment")
        assert result == ['mlcomment',"**\n///\n**"]

        g = Grammar("""/*
 * hello ** ..
 * abc
 */""")
        result,error = g.apply("mlcomment")
        assert result == ['mlcomment',"\n * hello ** ..\n * abc\n "]

    def test_something_star_no_slash(self):
        g = Grammar("""\
 hello *""")
        result,error = g.apply("something_star_no_slash")
        assert result == " hello *"

    def test_annotation(self):
        g = Grammar("""\
@abc""")
        result,error = g.apply("annotation")
        assert result == ['annotation', 'abc']

    def test_blocks(self):
        g = Grammar("""\
// hello""")
        result,error = g.apply("blocks")
        assert result == [["comment", " hello"]]
        
        g = Grammar("""
// hello
// hello""")
        result,error = g.apply("blocks")
        assert result == ['\n',["comment", " hello"],'\n',["comment", " hello"]]

        g = Grammar("""
/* hello */
// hello""")
        result,error = g.apply("blocks")
        assert result == ['\n',["mlcomment", " hello "],'\n',["comment", " hello"]]

        g = Grammar("""
/* hello
 * hello*/
// hello""")
        result,error = g.apply("blocks")
        assert result == ['\n',["mlcomment", " hello\n * hello"],'\n',["comment", " hello"]]

        g = Grammar("""
/* hello */
// hello
@abc""")
        result,error = g.apply("blocks")
        assert result == ['\n',["mlcomment", " hello "],'\n',["comment", " hello"], '\n', ['annotation','abc']]

