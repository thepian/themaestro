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

        g = Grammar("""@abc()""")
        result,error = g.apply("annotation")
        assert result == ['annotation', 'abc']

        g = Grammar("""@abc("url",5)""")
        result,error = g.apply("annotation")
        assert result == ['annotation', 'abc','"url",5']

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

    def test_k(self):
        g = Grammar("""typeof""")
        # result,error = g.apply("Keyword")
        # assert result == 'typeof'
        # result,error = g.apply("k","typeof")
        # assert result == 'typeof'
        
    def test_scanIdentifier(self):
        g = Grammar("""abc""")
        # result,error = g.apply("scanIdentifier")
        # assert result == 'abc'
        